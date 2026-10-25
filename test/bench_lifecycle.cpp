// Direct resource-state checks; no workload timing or performance assertions.
#include "../src/bench.cpp"
#include <cassert>
#include <sys/prctl.h>

// A protocol-only child leaves one helper in its process group at teardown.
static int ProtocolChild(const char *marker, int fd) {
    auto helper = fork();
    assert(helper >= 0);
    if (helper == 0) {
        close(fd); close(STDOUT_FILENO); close(STDERR_FILENO);
        for (;;) pause();
    }
    std::ofstream(marker) << getpid() << ' ' << helper << '\n';
    assert(::send(fd, "READY\n", 6, MSG_NOSIGNAL) == 6);
    char command;
    while (read(fd, &command, 1) == 1) {
        if (command == 'Q') {
            auto mode = std::filesystem::path(marker).parent_path().filename().string();
            if (mode == "signal") raise(SIGTERM);
            return mode == "exit" ? 7 : 0;
        }
        assert(command == 'C');
        const char *result = "10 20 1 4096 i64:1;\n";
        assert(::send(fd, result, strlen(result), MSG_NOSIGNAL) == (ssize_t)strlen(result));
    }
    return 124;
}

int main(int argc, char **argv) {
    using namespace goose;
    if (argc == 3) return ProtocolChild(argv[1], std::stoi(argv[2]));
    assert(argc == 2);
    Child child;
    int writers[2];
    for (int i = 0; i < 2; ++i) {
        int pipefd[2];
        assert(pipe(pipefd) == 0);
        child.logs[i] = pipefd[0]; writers[i] = pipefd[1];
        assert(fcntl(child.logs[i], F_SETFL, O_NONBLOCK) == 0);
        child.files[i] = tmpfile();
        assert(child.files[i]);
    }
    // EAGAIN is not EOF: future writes must still be drained.
    child.drain();
    assert(child.logs[0] >= 0 && child.logs[1] >= 0 && !child.log_failed);
    for (int i = 0; i < 2; ++i) {
        assert(write(writers[i], "log", 3) == 3);
        auto reader = child.logs[i];
        close(writers[i]);
        child.drain();
        assert(child.logs[i] == -1 && child.retained[i] == 3);
        assert(fcntl(reader, F_GETFD) == -1 && errno == EBADF);
        if (i == 0) assert(child.logs[1] >= 0);
        rewind(child.files[i]);
        char text[3];
        assert(fread(text, 1, sizeof text, child.files[i]) == 3);
        assert(string(text, 3) == "log");
    }
    child.drain();
    pollfd logs[2] {{child.logs[0], POLLIN, 0}, {child.logs[1], POLLIN, 0}};
    assert(poll(logs, 2, 0) == 0); // Closed logs cannot keep POLLHUP ready.
    assert(!child.log_failed);
    puts("benchmark lifecycle: log EOF closes readers; EAGAIN keeps readers open");

    // Adopt test helpers so the test can verify their terminal state and reap
    // them. The production supervisor does not need to adopt grandchildren.
    assert(prctl(PR_SET_CHILD_SUBREAPER, 1) == 0);
    for (auto mode : {"exit", "signal", "success"}) {
        auto directory = string(argv[1]) + '/' + mode;
        std::filesystem::create_directory(directory);
        auto marker = directory + "/pids";
        {
            BenchLock lock;
            assert(lock);
            BenchThermalOptions options; options.off = true;
            options.setup_timeout = options.sample_timeout = 2;
            vector<BenchProgram> programs {{std::filesystem::absolute(argv[0]).string(), marker, "small", directory}};
            auto code = RunBenchmarks(programs, false, 1, 5, options, nullptr, nullptr, &lock);
            assert(code == (string(mode) == "success" ? 0 : 1));
            pid_t group, helper;
            assert(std::ifstream(marker) >> group >> helper);
            int status = 0;
            // The direct child is already reaped. Group cleanup must still
            // have stopped the helper before the caller releases its lock.
            assert(waitpid(group, &status, WNOHANG) == -1 && errno == ECHILD);
            BenchLock occupied;
            assert(!occupied);
            bool killed = false;
            for (int attempt = 0; attempt < 200; ++attempt) {
                auto result = waitpid(helper, &status, WNOHANG);
                if (result == helper) {
                    killed = WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL;
                    helper = -1;
                    break;
                }
                assert(result == 0 || (result < 0 && errno == EINTR));
                poll(nullptr, 0, 10);
            }
            // Remove a surviving helper even if this regression check fails.
            if (helper > 0) {
                kill(helper, SIGKILL);
                while (waitpid(helper, &status, 0) < 0 && errno == EINTR) {}
            }
            assert(killed);
        }
        BenchLock released;
        assert(released);
    }
    puts("benchmark lifecycle: helpers stopped after failed, signaled and normal teardown; lock released");
}
