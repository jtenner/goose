// Linux process adapter. Control never shares stdout/stderr with the workload.
#include <algorithm>
#include <string>
#include <vector>
#include <cstdio>
#include <stdexcept>
#include <chrono>
#include <cerrno>
#include <cstring>
using std::string; using std::vector;
#include "bench.h"
#ifdef __linux__
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/poll.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#endif
namespace goose {
#ifdef __linux__
string BenchDirectory() {
    char path[] = "/tmp/goose-bench-XXXXXX";
    if (!mkdtemp(path)) throw std::runtime_error("cannot create benchmark artifact directory");
    return path;
}
namespace {
volatile sig_atomic_t interrupted = 0;
void BenchInterrupt(int) { interrupted = 1; }
struct Child {
    int fd = -1;
    pid_t pid = -1;
    string out, err;
    int logs[2] { -1, -1 };
    FILE *files[2] { nullptr, nullptr };
    size_t retained[2] {};
    bool truncated = false;
    void drain() {
        char buffer[8192];
        for (int i = 0; i < 2; ++i) {
            if (logs[i] < 0) continue;
            // Bound each turn as well as retained data: an endless writer
            // cannot starve the control channel or its timeout.
            for (int turn = 0; turn < 32; ++turn) {
                auto n = read(logs[i], buffer, sizeof buffer);
                if (n <= 0) break;
                auto keep = std::min((size_t)n, 1048576 - retained[i]);
                if (keep) fwrite(buffer, 1, keep, files[i]);
                retained[i] += keep;
                truncated |= keep < (size_t)n;
            }
        }
    }
    ~Child() {
        if (fd >= 0) close(fd);
        drain();
        for (int i = 0; i < 2; ++i) {
            if (logs[i] >= 0) close(logs[i]);
            if (files[i]) fclose(files[i]);
        }
        if (pid > 0) { kill(-pid, SIGKILL); while (waitpid(pid, nullptr, 0) < 0 && errno == EINTR) {} }
    }
    void send(char c) {
        if (::send(fd, &c, 1, MSG_NOSIGNAL) != 1) throw std::runtime_error("benchmark control channel closed");
    }
    string line(const char *phase) {
        string text;
        auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(600);
        while (text.size() < 1048576) {
            if (interrupted) throw std::runtime_error("benchmark interrupted");
            auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - std::chrono::steady_clock::now()).count();
            if (ms <= 0) throw std::runtime_error(string(phase) + " timeout");
            drain();
            pollfd p[3] { { fd, POLLIN, 0 }, { logs[0], POLLIN, 0 }, { logs[1], POLLIN, 0 } };
            auto ready = poll(p, 3, (int)ms);
            if (ready < 0 && errno == EINTR) continue;
            if (ready <= 0) throw std::runtime_error(string(phase) + " timeout or control error");
            if (!(p[0].revents & (POLLIN | POLLHUP | POLLERR))) continue;
            char c;
            if (read(fd, &c, 1) != 1) throw std::runtime_error(string(phase) + " failed: child exited before response");
            if (c == '\n') return text;
            text += c;
        }
        throw std::runtime_error("benchmark control response too large");
    }
    void start(const BenchProgram &p, int id) {
        int pair[2];
        if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair)) throw std::runtime_error("cannot create benchmark control channel");
        out = p.directory + "/child-" + std::to_string(id) + ".stdout";
        err = p.directory + "/child-" + std::to_string(id) + ".stderr";
        int output[2], errors[2];
        if (pipe(output) || pipe(errors)) { close(pair[0]); close(pair[1]); throw std::runtime_error("cannot create benchmark log pipes"); }
        logs[0] = output[0]; logs[1] = errors[0];
        files[0] = fopen(out.c_str(), "wb"); files[1] = fopen(err.c_str(), "wb");
        if (!files[0] || !files[1]) throw std::runtime_error("cannot create benchmark logs");
        fcntl(logs[0], F_SETFL, O_NONBLOCK); fcntl(logs[1], F_SETFL, O_NONBLOCK);
        auto arg = std::to_string(pair[1]);
        pid = fork();
        if (pid == 0) {
            setpgid(0, 0);
            close(pair[0]);
            close(logs[0]); close(logs[1]);
            if (dup2(output[1], 1) < 0 || dup2(errors[1], 2) < 0) _exit(126);
            close(output[1]); close(errors[1]);
            execl(p.executable.c_str(), p.executable.c_str(), p.key.c_str(), arg.c_str(), (char *)nullptr);
            _exit(127);
        }
        close(output[1]); close(errors[1]);
        close(pair[1]); fd = pair[0];
        if (pid < 0) throw std::runtime_error("cannot launch benchmark child");
        setpgid(pid, pid);
        if (line("setup") != "READY") throw std::runtime_error("invalid benchmark readiness response");
    }
    void finish() {
        send('Q');
        // Read EOF under the same bounded deadline before reaping.
        if (!lineExit()) throw std::runtime_error("benchmark child failed during teardown");
        drain();
        if (retained[0] || retained[1])
            fprintf(stderr, "benchmark emitted output%s; logs: %s %s\n", truncated ? " (truncated at 1 MiB per stream)" : "", out.c_str(), err.c_str());
    }
    bool lineExit() {
        auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(600);
        int status;
        for (;;) {
            if (interrupted) throw std::runtime_error("benchmark interrupted");
            drain();
            auto r = waitpid(pid, &status, WNOHANG);
            if (r == pid) { pid = -1; return WIFEXITED(status) && WEXITSTATUS(status) == 0; }
            if (r < 0 && errno != EINTR) return false;
            if (std::chrono::steady_clock::now() >= deadline) throw std::runtime_error("benchmark teardown timeout");
            poll(nullptr, 0, 10);
        }
    }
};
}
int RunBenchmarks(const vector<BenchProgram> &programs, bool fresh, int warmups, int samples) {
    int lock = open("/tmp/goose-shared-native-benchmark.lock", O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (lock < 0 || flock(lock, LOCK_EX | LOCK_NB)) {
        if (lock >= 0) close(lock);
        fprintf(stderr, "bench: shared-native benchmark lock unavailable or occupied\n");
        return 2;
    }
    struct Unlock { int fd; ~Unlock() { close(fd); } } unlock { lock };
    fprintf(stderr, "UNGATED experimental bench: thermal supervision unavailable in stage 2; raw function timings only\n");
    struct Signals {
        struct sigaction oldint {}, oldterm {};
        Signals() {
            interrupted = 0;
            struct sigaction action {};
            action.sa_handler = BenchInterrupt;
            sigemptyset(&action.sa_mask);
            sigaction(SIGINT, &action, &oldint);
            sigaction(SIGTERM, &action, &oldterm);
        }
        ~Signals() { sigaction(SIGINT, &oldint, nullptr); sigaction(SIGTERM, &oldterm, nullptr); }
    } signals;
    int childid = 0;
    try {
        for (auto &p : programs) {
            string expected;
            Child reused;
            if (!fresh) reused.start(p, ++childid);
            for (int i = 0; i < warmups + samples; ++i) {
                Child one;
                auto &child = fresh ? one : reused;
                if (fresh) child.start(p, ++childid);
                child.send('C');
                auto response = child.line("sample");
                unsigned long long start, end;
                int finite, offset = 0;
                if (sscanf(response.c_str(), "%llu %llu %d %n", &start, &end, &finite, &offset) != 3 || !offset || end <= start)
                    throw std::runtime_error("invalid benchmark timed result");
                auto checksum = response.substr(offset);
                if (!finite) throw std::runtime_error("nonfinite benchmark checksum: " + checksum);
                if (expected.empty()) expected = checksum;
                else if (expected != checksum)
                    throw std::runtime_error("checksum disagreement for " + p.key + " (" + p.size + "): expected " + expected + ", observed " + checksum);
                printf("%s\t%s\t%s\t%d\t%llu ns\t%s\n", p.key.c_str(), p.size.c_str(),
                       i < warmups ? "warmup" : "measure", i < warmups ? i + 1 : i - warmups + 1, end - start, checksum.c_str());
                if (end - start < 1000) fprintf(stderr, "benchmark %s: very short call; timer resolution/bridge overhead may dominate\n", p.key.c_str());
                if (fresh) child.finish();
            }
            if (!fresh) reused.finish();
        }
        return 0;
    } catch (const std::exception &e) {
        fprintf(stderr, "bench: %s\n", e.what());
        return interrupted ? 130 : 1;
    }
}
#else
string BenchDirectory() { throw std::runtime_error("benchmark execution currently requires Linux"); }
int RunBenchmarks(const vector<BenchProgram> &, bool, int, int) { return 2; }
#endif
}
