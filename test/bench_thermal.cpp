// Supervisor integration with a scripted sensor and virtual gate clock.
#include "../src/bench.cpp"
#include <cassert>
int main(int argc, char **argv) {
    using namespace goose;
    assert(argc == 4);
    string scenario = argv[3];
    // Real hwmon adapter against files: both sockets matter; Tdie is rejected.
    if (scenario == "adapter") {
        string directory = argv[2];
        std::ofstream(directory + "/name") << "scripted_cpu\n";
        std::ofstream(directory + "/temp1_label") << "Tctl\n";
        std::ofstream(directory + "/temp2_label") << "Tctl\n";
        std::ofstream(directory + "/temp1_input") << "60000\n";
        std::ofstream(directory + "/temp2_input") << "70000\n";
        BenchThermalOptions o;
        o.sensors = {directory + "/temp1_input", directory + "/temp2_input"};
        Hwmon hwmon(o, directory);
        assert(hwmon.read() == 70);
        std::ofstream(directory + "/temp2_input") << "59000\n";
        assert(hwmon.read() == 60);
        std::ofstream(directory + "/temp2_label") << "Tdie\n";
        bool invalid = false;
        try { Hwmon bad(o, directory); } catch (...) { invalid = true; }
        assert(invalid);
        std::filesystem::remove(directory + "/temp1_input");
        invalid = false;
        try { hwmon.read(); } catch (...) { invalid = true; }
        assert(invalid);
        return 0;
    }

    vector<double> readings;
    if (scenario == "retry-process" || scenario == "retry" || scenario == "exhaust" || scenario == "mismatch") readings = {60, 70, 70, 60};
    else if (scenario == "wait" || scenario == "cancel") readings = {70, 61, 60};
    else if (scenario == "loss") readings = {60};
    double clock = 0; size_t index = 0; int waits = 0;
    BenchThermalOptions options;
    options.poll_ms = scenario == "mid" ? 1 : 1000000; options.retries = scenario == "exhaust" ? 0 : 10;
    options.off = scenario == "off";
    BenchThermalSource source {
        [&] { if (scenario == "absent" || scenario == "off") throw std::runtime_error("no readable Tctl sensor"); },
        [&] {
            if (scenario == "mid") {
                ++index;
                if (index == 2) std::ofstream(string(argv[2]) + "/crossed") << "crossed";
                return index == 2 ? 70.0 : 60.0;
            }
            if (scenario == "loss" && index) throw std::runtime_error("temperature read failed: disappeared");
            return index < readings.size() ? readings[index++] : 60;
        },
        [&] { return clock; },
        [&](double seconds) { if (scenario == "cancel") { interrupted = 1; throw std::runtime_error("benchmark interrupted"); } clock += seconds; ++waits; }
    };
    vector<BenchProgram> programs {{argv[1], "entry", "medium", argv[2]}};
    int result = RunBenchmarks(programs, scenario == "retry-process", 1, 5, options, &source);
    if (scenario == "wait") assert(waits == 2);
    if (scenario == "retry") assert(waits == 1);
    if (scenario == "off") assert(index == 0);
    // Deterministic monitor state: crossing is observed without any wait or
    // suspension, equality is accepted, rejected peaks survive the post-read.
    scenario = "unit";
    readings = {60, 66, 60}; index = 0; waits = 0;
    BenchThermal monitor {options, [&] { return readings.at(index++); }, source.now, source.wait};
    monitor.options.off = false;
    monitor.gate(); clock += .05; monitor.observe(); clock += .05;
    assert(!monitor.finish() && monitor.maximum == 66 && waits == 0);
    assert(monitor.gap >= .05 - 1e-9);
    readings = {60, 65}; index = 0; monitor.gate(); assert(monitor.finish());
    readings = {70}; index = 0; monitor.options.gate_timeout = 2;
    monitor.read = [] { return 70; };
    bool timeout = false;
    try { monitor.gate(); } catch (const std::runtime_error &) { timeout = true; }
    assert(timeout);
    return result;
}
