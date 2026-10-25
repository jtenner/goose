// Direct resource-state checks; no workload timing or performance assertions.
#include "../src/bench.cpp"
#include <cassert>

int main() {
    using namespace goose;
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
}
