// Injectable thermal policy: production supplies hwmon reads and monotonic waits.
#pragma once
#include <functional>
#include <algorithm>
#include <vector>
#include <string>
#include <cmath>
#include <stdexcept>
namespace goose {
struct BenchThermalOptions {
    bool off = false;
    double gate = 60, ceiling = 65, poll_ms = 50, gate_timeout = 300;
    double sample_timeout = 600, setup_timeout = 600;
    int retries = 10;
    std::vector<std::string> sensors;
};
struct BenchThermalSource {
    std::function<void()> preflight;
    std::function<double()> read, now;
    std::function<void(double)> wait;
};
struct BenchThermal {
    BenchThermalOptions options;
    std::function<double()> read, now;
    std::function<void(double)> wait;
    double current = 0, maximum = 0, last = 0, gap = 0, waited = 0;
    bool active = false;
    double observe() {
        double value = read(), time = now();
        if (!std::isfinite(value)) throw std::runtime_error("temperature read failed");
        if (active) gap = std::max(gap, time - last);
        maximum = active ? std::max(maximum, value) : value;
        last = time; active = true;
        current = value; return value;
    }
    void gate() {
        active = false; gap = 0;
        if (options.off) return;
        double start = now();
        while (observe() > options.gate) {
            double remaining = options.gate_timeout - (now() - start);
            if (remaining <= 0) throw std::runtime_error("temperature gate timeout");
            wait(std::min(1.0, remaining));
        }
        waited = now() - start;
        // The final gate read is the pre-release bracket.
        maximum = current;

    }
    bool finish() { if (options.off) return true; observe(); return maximum <= options.ceiling; }
};
}
