// Linux process adapter. Control never shares stdout/stderr with the workload.
#include <algorithm>
#include <string>
#include <vector>
#include <cstdio>
#include <stdexcept>
#include <chrono>
#include <cerrno>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <limits>
using std::string; using std::vector;
#include "bench.h"
#include "bench_results.h"
#ifdef __linux__
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/poll.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <sys/resource.h>
#include <charconv>
#endif
namespace goose {
#ifdef __linux__
string BenchDirectory() {
    char path[] = "/tmp/goose-bench-XXXXXX";
    if (!mkdtemp(path)) throw std::runtime_error("cannot create benchmark artifact directory");
    return path;
}
namespace {
string ErrorCode(const string &message) {
    if (message.find("interrupted") != string::npos) return "interrupted";
    if (message.find("clock resolution") != string::npos) return "clock";
    if (message.find("checksum") != string::npos && message.find("protocol") == string::npos) return "checksum";
    if (message.find("timeout") != string::npos) return "timeout";
    if (message.find("thermal_retries") != string::npos) return "thermal_retries";
    if (message.find("temperature") != string::npos || message.find("Tctl") != string::npos) return "sensor";
    if (message.find("teardown") != string::npos || message.find("child exited") != string::npos) return "child_exit";
    if (message.find("setup") != string::npos) return "setup";
    if (message.find("cannot ") != string::npos) return "io";
    return "protocol";
}
volatile sig_atomic_t interrupted = 0;
void BenchInterrupt(int) { interrupted = 1; }
BenchAttempt DecodeAttempt(const string &response, int child, bool warmup, int slot) {
    uint64_t values[4] {}; size_t offset = 0;
    for (auto &value : values) {
        auto space = response.find(' ',offset);
        if (space == string::npos) throw std::runtime_error("invalid benchmark timed result protocol");
        auto parsed = std::from_chars(response.data()+offset,response.data()+space,value);
        if (parsed.ec != std::errc() || parsed.ptr != response.data()+space)
            throw std::runtime_error("invalid benchmark timed result protocol");
        offset = space+1;
    }
    if (values[2] > 1) throw std::runtime_error("invalid benchmark finite flag protocol");
    BenchAttempt a; a.child_id = child; a.warmup = warmup; a.slot = slot;
    a.start_ns = values[0]; a.end_ns = values[1]; a.finite = values[2] != 0; a.completed = true;
    a.rss = values[3];
    auto payload = response.substr(offset);
    while (!payload.empty()) {
        auto colon = payload.find(':'), semi = payload.find(';');
        if (colon == string::npos || semi == string::npos || colon >= semi || colon == 0 || colon + 1 == semi)
            throw std::runtime_error("invalid benchmark checksum protocol");
        a.checksum.push_back({ payload.substr(0, colon), payload.substr(colon + 1, semi - colon - 1) });
        payload.erase(0, semi + 1);
    }
    if (a.checksum.empty()) throw std::runtime_error("missing benchmark checksum");
    return a;
}
string ChecksumText(const vector<BenchComponent> &components) {
    string text;
    for (auto &c : components) text += c.type + ":" + c.value + ";";
    return text;
}
void PrintAttempt(const BenchProgram &p, const BenchAttempt &a) {
    printf("%s\t%s\t%s\t%d\t%llu ns\t%s\n", p.key.c_str(), p.size.c_str(),
           a.warmup ? "warmup" : "measure", a.slot,
           (unsigned long long)(a.end_ns - a.start_ns), ChecksumText(a.checksum).c_str());
    fflush(stdout);
}
double ThermalNow() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
struct Hwmon {
    vector<string> paths;
    std::ofstream trace;
    vector<double> last_reads;
    vector<BenchTemperatureRead> last_batch, captured;
    vector<string> descriptors;
    bool capturing = false;
    double maximum_gap = 0;
    void resetCoverage() { maximum_gap = 0; captured = last_batch; capturing = true; }
    static string text(const string &path) {
        std::ifstream in(path); string value;
        if (!std::getline(in, value)) throw std::runtime_error("temperature read failed: " + path);
        return value;
    }
    explicit Hwmon(const BenchThermalOptions &options, const string &directory) {
        namespace fs = std::filesystem;
        if (options.off) return;
        trace.open(directory + "/temperature.log");
        if (!trace) throw std::runtime_error("cannot create temperature trace");
        paths = options.sensors;
        if (paths.empty()) {
            std::error_code ec;
            for (auto &chip : fs::directory_iterator("/sys/class/hwmon", ec)) {
                for (auto &entry : fs::directory_iterator(chip.path(), ec)) {
                    auto name = entry.path().filename().string();
                    if (name.starts_with("temp") && name.ends_with("_label") && text(entry.path()) == "Tctl")
                        paths.push_back(entry.path().string().substr(0, entry.path().string().size() - 6) + "_input");
                }
            }
        }
        if (paths.empty()) throw std::runtime_error("no readable Tctl sensor; use --temperature off for an explicit UNGATED run");
        for (auto &path : paths) {
            std::error_code path_error;
            auto canonical = fs::canonical(path, path_error);
            if (path_error) throw std::runtime_error("temperature read failed: " + path);
            path = canonical.string();
            if (!path.ends_with("_input") || text(path.substr(0, path.size() - 6) + "_label") != "Tctl")
                throw std::runtime_error("temperature sensor must have associated Tctl label: " + path);
            auto parent = fs::path(path).parent_path();
            std::error_code ec;
            auto device = fs::canonical(parent / "device", ec);
            if (ec) device = fs::canonical(parent);
            if (std::any_of(descriptors.begin(), descriptors.end(), [&](const string &d) { return d == BenchObject({{"id", BenchString(path)}, {"chip", BenchString(text((parent / "name").string()))}, {"device_path", BenchString(device.string())}, {"label", BenchString("Tctl")}, {"input_path", BenchString(path)}}); }))
                throw std::runtime_error("duplicate temperature sensor: " + path);
            descriptors.push_back(BenchObject({{"id", BenchString(path)}, {"chip", BenchString(text((parent / "name").string()))}, {"device_path", BenchString(device.string())}, {"label", BenchString("Tctl")}, {"input_path", BenchString(path)}}));
            fprintf(stderr, "Tctl sensor: chip=%s device=%s label=Tctl input=%s%s\n",
                    text((parent / "name").string()).c_str(), device.c_str(), path.c_str(),
                    options.sensors.empty() ? "" : " (explicit sensor restriction)");
        }
        last_reads.resize(paths.size());
        read(); // Preflight before any initializer.
    }
    double read() {
        double maximum = -std::numeric_limits<double>::infinity();
        last_batch.clear();
        for (size_t i = 0; i < paths.size(); ++i) {
            auto &path = paths[i];
            auto value = text(path); size_t end;
            double c;
            try { c = (double)std::stoll(value, &end) / 1000; }
            catch (...) { throw std::runtime_error("temperature read failed: " + path); }
            if (end != value.size() || !std::isfinite(c)) throw std::runtime_error("temperature read failed: " + path);
            double time = ThermalNow();
            if (last_reads[i]) maximum_gap = std::max(maximum_gap, time - last_reads[i]);
            last_reads[i] = time;
            auto ns = (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
            last_batch.push_back({path, ns, c});
            if (capturing) captured.push_back(last_batch.back());
            trace << ns
                  << "\t" << path << "\t" << c << "\n";
            trace.flush();
            if (!trace) throw std::runtime_error("cannot retain temperature trace");
            maximum = std::max(maximum, c);
        }
        return maximum;
    }
};
struct Child {
    int fd = -1;
    pid_t pid = -1;
    string out, err, log_prefix;
    int logs[2] { -1, -1 };
    FILE *files[2] { nullptr, nullptr };
    size_t retained[2] {};
    bool truncated = false;
    BenchChild *record = nullptr;
    BenchRow *row = nullptr;
    double shutdown_timeout = 600;
    void reaped(int status, const rusage &usage) {
        if (!record) return;
        if (WIFEXITED(status)) record->exit_code = WEXITSTATUS(status);
        if (WIFSIGNALED(status)) record->signal = WTERMSIG(status);
        record->rss = uint64_t(usage.ru_maxrss) * 1024;
        row->rss = std::max(row->rss.value_or(0), *record->rss);
        row->memory_reason.clear();
    }
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
                if (record) record->logs_truncated = truncated;
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
        if (pid > 0) {
            kill(-pid, SIGKILL); int status = 0; rusage usage {};
            pid_t result; do { result = wait4(pid, &status, 0, &usage); } while (result < 0 && errno == EINTR);
            if (result > 0) reaped(status, usage);
        }
        if (record) record->logs_truncated = truncated;
    }
    void send(char c) {
        if (::send(fd, &c, 1, MSG_NOSIGNAL) != 1) throw std::runtime_error("benchmark control channel closed");
    }
    string line(const char *phase, double timeout = 600, BenchThermal *thermal = nullptr) {
        string text;
        auto deadline = ThermalNow() + timeout;
        double next = ThermalNow() + (thermal ? thermal->options.poll_ms / 1000 : timeout);
        while (text.size() < 1048576) {
            if (interrupted) throw std::runtime_error("benchmark interrupted");
            auto time = ThermalNow();
            if (thermal && time >= next) { thermal->observe(); next = ThermalNow() + thermal->options.poll_ms / 1000; }
            auto ms = (deadline - ThermalNow()) * 1000;
            if (ms <= 0) throw std::runtime_error(string(phase) + " timeout");
            drain();
            pollfd p[3] { { fd, POLLIN, 0 }, { logs[0], POLLIN, 0 }, { logs[1], POLLIN, 0 } };
            auto ready = poll(p, 3, (int)std::min(1000.0, std::max(1.0, std::min(ms, (next - ThermalNow()) * 1000))));
            if (ready < 0 && errno == EINTR) continue;
            if (ready == 0) continue;
            if (ready < 0) throw std::runtime_error(string(phase) + " timeout or control error");
            if (!(p[0].revents & (POLLIN | POLLHUP | POLLERR))) continue;
            char c;
            if (read(fd, &c, 1) != 1) throw std::runtime_error(string(phase) + " failed: child exited before response");
            if (c == '\n') return text;
            text += c;
        }
        throw std::runtime_error("benchmark control response too large");
    }
    void start(const BenchProgram &p, int id, double timeout) {
        int pair[2];
        if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair)) throw std::runtime_error("cannot create benchmark control channel");
        out = p.directory + "/child-" + log_prefix + std::to_string(id) + ".stdout";
        err = p.directory + "/child-" + log_prefix + std::to_string(id) + ".stderr";
        if (record) { record->stdout_path = out; record->stderr_path = err; }
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
        if (line("setup", timeout) != "READY") throw std::runtime_error("invalid benchmark readiness response");
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
        auto deadline = ThermalNow() + shutdown_timeout;
        int status;
        for (;;) {
            if (interrupted) throw std::runtime_error("benchmark interrupted");
            drain();
            rusage usage {};
            auto r = wait4(pid, &status, WNOHANG, &usage);
            if (r == pid) { reaped(status, usage); pid = -1; return WIFEXITED(status) && WEXITSTATUS(status) == 0; }
            if (r < 0 && errno != EINTR) return false;
            if (ThermalNow() >= deadline) throw std::runtime_error("benchmark teardown timeout");
            poll(nullptr, 0, 10);
        }
    }
};
}
int RunBenchmarks(const vector<BenchProgram> &programs, bool fresh, int warmups, int samples, const BenchThermalOptions &options, BenchThermalSource *source, BenchReport *report) {
    int lock = open("/tmp/goose-shared-native-benchmark.lock", O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (lock < 0 || flock(lock, LOCK_EX | LOCK_NB)) {
        if (lock >= 0) close(lock);
        fprintf(stderr, "bench: shared-native benchmark lock unavailable or occupied\n");
        if (report) report->error = {"lock", "shared-native benchmark lock unavailable or occupied"};
        return 2;
    }
    struct Unlock { int fd; ~Unlock() { close(fd); } } unlock { lock };

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
    bool preflight = true;
    try {
        if (options.gate > options.ceiling) throw std::runtime_error("temperature gate must be <= ceiling");
        std::unique_ptr<Hwmon> sensors;
        if (source) { if (!options.off) source->preflight(); }
        else sensors = std::make_unique<Hwmon>(options, programs.at(0).directory);
        BenchThermal thermal {options, [&] { return source ? source->read() : sensors->read(); }, ThermalNow, [](double seconds) {
            double deadline = ThermalNow() + seconds;
            while (ThermalNow() < deadline) {
                if (interrupted) throw std::runtime_error("benchmark interrupted");
                poll(nullptr, 0, (int)std::max(1.0, std::min(50.0, (deadline - ThermalNow()) * 1000)));
            }
        }};
        if (source) { thermal.now = source->now; thermal.wait = source->wait; }
        if (options.off) fprintf(stderr, "UNGATED thermal_mode=disabled reason=explicit --temperature off\n");
        else fprintf(stderr, "thermal_mode=required gate=%.3f C ceiling=%.3f C poll=%.3f ms\n", options.gate, options.ceiling, options.poll_ms);
        preflight = false;
        vector<BenchRow> localrows(programs.size());
        auto &rows = report ? report->rows : localrows;
        if (report && sensors) report->sensors = sensors->descriptors;
        for (size_t rowindex = 0; rowindex < programs.size(); ++rowindex) {
            auto &p = programs[rowindex];
            auto &row = rows[rowindex];
            row.status = "running";
            auto startChild = [&](Child &child) {
                row.children.push_back({});
                child.record = &row.children.back(); child.record->id = ++childid;
                if (report) child.log_prefix = report->run_id + "-";
                if (report) child.log_prefix = report->run_id + "-";
                child.row = &row; child.shutdown_timeout = options.sample_timeout;
                child.start(p, childid, options.setup_timeout);
            };
            try {
                Child reused;
                if (!fresh) startChild(reused);
                for (int i = 0; i < warmups + samples; ++i) {
                    for (int retry = 0;; ++retry) {
                        Child one;
                        auto &child = fresh ? one : reused;
                        if (fresh) startChild(child);
                        row.attempts.push_back({});
                        auto &a = row.attempts.back();
                        a.child_id = childid; a.warmup = i < warmups;
                        a.slot = i < warmups ? i + 1 : i - warmups + 1; a.retry = retry;
                        auto gate_start = thermal.now();
                        try {
                            if (sensors) sensors->capturing = false;
                            thermal.gate();
                            a.gate_wait_seconds = thermal.waited;
                            if (!options.off) a.before = thermal.current;
                            if (sensors) sensors->resetCoverage();
                            if (interrupted) throw std::runtime_error("benchmark interrupted");
                            child.send('C');
                            auto response = child.line("sample", options.sample_timeout, options.off ? nullptr : &thermal);
                            auto decoded = DecodeAttempt(response, childid, a.warmup, a.slot);
                            a.start_ns = decoded.start_ns; a.end_ns = decoded.end_ns;
                            a.finite = decoded.finite; a.completed = true; a.checksum = std::move(decoded.checksum); a.rss = decoded.rss;
                            bool accepted = thermal.finish();
                            if (!options.off) {
                                a.after = thermal.current; a.temperature_max = thermal.maximum;
                                a.poll_gap_ms = (sensors ? sensors->maximum_gap : thermal.gap) * 1000;
                                if (sensors) { a.reads = sensors->captured; sensors->capturing = false; }
                                row.temperature_max = std::max(row.temperature_max.value_or(thermal.maximum), thermal.maximum);
                            }
                            BenchRecordAttempt(row, a, accepted);
                            if (!report) PrintAttempt(p, a);
                            if (a.end_ns - a.start_ns < 1000) fprintf(stderr, "benchmark %s: very short call; timer resolution/bridge overhead may dominate\n", p.key.c_str());
                            if (!options.off) fprintf(stderr, "thermal %s %s %s slot=%d retry=%d status=%s maximum_observed_Tctl=%.3f C max_poll_gap=%.3f ms gate_wait=%.3f s\n",
                                p.key.c_str(), p.size.c_str(), a.warmup ? "warmup" : "measure", a.slot, retry,
                                a.status.c_str(), thermal.maximum, *a.poll_gap_ms, thermal.waited);
                            if (report) report->Checkpoint();
                            if (fresh) child.finish();
                            if (accepted) break;
                            if (retry >= options.retries) throw std::runtime_error("thermal_retries exhausted");
                        } catch (const std::exception &e) {
                            if (!a.start_ns) a.gate_wait_seconds = thermal.now() - gate_start;
                            if (sensors && a.start_ns) {
                                a.reads = sensors->captured; sensors->capturing = false;
                                for (auto &reading:a.reads) a.temperature_max = std::max(a.temperature_max.value_or(reading.c),reading.c);
                                if (a.temperature_max) row.temperature_max = std::max(row.temperature_max.value_or(*a.temperature_max),*a.temperature_max);
                                a.poll_gap_ms = sensors->maximum_gap * 1000;
                            }
                            if (a.status != "thermal_rejected") {
                                a.status = interrupted ? "interrupted" : "failed";
                                a.error = {ErrorCode(e.what()), e.what()};
                            }
                            throw;
                        }
                    }
                }
                if (!fresh) reused.finish();
                BenchCompleteRow(row, warmups, samples);
                if (report) report->Checkpoint();
            } catch (const std::exception &e) {
                row.status = interrupted ? "interrupted" : "failed"; row.summary.reset();
                row.error = {ErrorCode(e.what()), e.what()};
                throw;
            }
        }
        return 0;
    } catch (const std::exception &e) {
        fprintf(stderr, "bench: %s\n", e.what());
        if (report) {
            report->error = {ErrorCode(e.what()), e.what()};
            if (preflight && !options.off) report->thermal_reason = e.what();
        }
        return interrupted ? 130 : preflight ? 2 : 1;
    }
}
#else
string BenchDirectory() { throw std::runtime_error("benchmark execution currently requires Linux"); }
int RunBenchmarks(const vector<BenchProgram> &, bool, int, int, const BenchThermalOptions &, BenchThermalSource *, BenchReport *) { return 2; }
#endif
}
