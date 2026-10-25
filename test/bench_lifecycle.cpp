// Direct resource-state checks; no workload timing or performance assertions.
#include <signal.h>
#include <cerrno>
#include <unistd.h>
#include <sys/file.h>
#include <fcntl.h>
#include <cassert>
// Model a successful kill whose delivery is still pending, or a syscall
// failure. A group-state probe delivers the pending signal. No test wait
// can make an unchecked production stop appear complete.
enum class KillFault { None, Deferred, Denied, Interrupted };
static KillFault kill_fault = KillFault::None;
static pid_t pending_group = -1;
static int LifecycleKill(pid_t pid, int signal) {
    if (pid < 0 && signal == SIGKILL && kill_fault != KillFault::None) {
        int lock = open("/tmp/goose-shared-native-benchmark.lock", O_RDWR | O_CLOEXEC);
        assert(lock >= 0);
        assert(flock(lock, LOCK_EX | LOCK_NB) < 0 && errno == EWOULDBLOCK);
        close(lock);
        auto fault = kill_fault;
        kill_fault = KillFault::None;
        if (fault == KillFault::Deferred) { pending_group = pid; return 0; }
        errno = fault == KillFault::Denied ? EPERM : EINTR;
        return -1;
    }
    if (pid == pending_group && signal == 0) {
        ::kill(pid, SIGKILL);
        pending_group = -1;
    }
    return ::kill(pid, signal);
}
#define kill LifecycleKill
#include "../src/bench.cpp"
#undef kill
#include <cassert>
#include <sys/prctl.h>

// A protocol-only child leaves one helper in its process group at teardown.
static int ProtocolChild(const char *marker, int fd) {
    // The next row/process must not start while the previous group exists.
    pid_t old_group, old_helper;
    std::ifstream previous(marker);
    while (previous >> old_group >> old_helper)
        if (kill(-old_group, 0) == 0 || errno != ESRCH) return 123;
    auto mode = std::filesystem::path(marker).parent_path().filename().string();
    auto helper = fork();
    assert(helper >= 0);
    if (helper == 0) {
        close(fd); close(STDOUT_FILENO); close(STDERR_FILENO);
        for (;;) pause();
    }
    std::ofstream(marker, std::ios::app) << getpid() << ' ' << helper << '\n';
    if (mode == "setup") { ::send(fd, "BAD\n", 4, MSG_NOSIGNAL); for (;;) pause(); }
    assert(::send(fd, "READY\n", 6, MSG_NOSIGNAL) == 6);
    char command;
    while (read(fd, &command, 1) == 1) {
        if (command == 'Q') {
            if (mode == "signal") raise(SIGTERM);
            return mode == "exit" ? 7 : 0;
        }
        assert(command == 'C');
        if (mode == "sample") { ::send(fd, "BAD\n", 4, MSG_NOSIGNAL); continue; }
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

    int scenarios = 0;
    for (auto mode : {"deferred", "denied", "interrupted", "exit", "signal", "setup", "sample",
                      "fresh", "next-row", "inherited"}) {
        auto directory = string(argv[1]) + '/' + mode;
        std::filesystem::create_directory(directory);
        auto marker = directory + "/pids";
        // Most cases run without a test subreaper. The inherited case also
        // checks that production preserves an existing caller setting.
        int inherited = string(mode) == "inherited" || string(mode) == "deferred";
        assert(prctl(PR_SET_CHILD_SUBREAPER, inherited) == 0);
        kill_fault = string(mode) == "deferred" ? KillFault::Deferred :
                     string(mode) == "denied" ? KillFault::Denied :
                     string(mode) == "interrupted" ? KillFault::Interrupted : KillFault::None;
        BenchThermalOptions options; options.off = true;
        options.setup_timeout = options.sample_timeout = 2;
        vector<BenchProgram> programs {{std::filesystem::absolute(argv[0]).string(), marker, "small", directory}};
        if (string(mode) == "next-row") programs.push_back(programs.front());
        auto code = RunBenchmarks(programs, string(mode) == "fresh", 1, 5, options);
        // This is the production release point: RunBenchmarks owned its lock.
        // Observe state immediately, with no test-only wait or reap first.
        BenchLock released;
        assert(released);
        bool gone = true;
        pid_t group, helper;
        int groups = 0;
        std::ifstream pids(marker);
        while (pids >> group >> helper) {
            ++groups;
            bool group_gone = kill(-group, 0) < 0 && errno == ESRCH;
            bool helper_gone = kill(helper, 0) < 0 && errno == ESRCH;
            gone &= group_gone && helper_gone;
            int status;
            assert(waitpid(group, &status, WNOHANG) == -1 && errno == ECHILD);
            if (!helper_gone) {
                // Emergency cleanup only after recording failure. This cannot
                // turn a failed release-point observation into a pass.
                kill(-group, SIGKILL);
                while (waitpid(helper, &status, 0) < 0 && errno == EINTR) {}
            }
        }
        assert(groups > 0);
        assert(gone && "production released the lock before group cleanup completed");
        bool failure = string(mode) == "exit" || string(mode) == "signal" || string(mode) == "setup" ||
                       string(mode) == "sample" || string(mode) == "denied";
        assert(code == (failure ? 1 : 0));
        assert(groups == (string(mode) == "fresh" ? 6 : string(mode) == "next-row" ? 2 : 1));
        int restored = -1;
        assert(prctl(PR_GET_CHILD_SUBREAPER, &restored) == 0 && restored == inherited);
        ++scenarios;
    }
    assert(prctl(PR_SET_CHILD_SUBREAPER, 0) == 0);
    printf("benchmark lifecycle: %d production cleanup scenarios passed; lock released after helpers reaped\n", scenarios);
}
