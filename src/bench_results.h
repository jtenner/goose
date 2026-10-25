// Transport-independent benchmark records. All consumers use these records.
#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
namespace goose {
struct BenchComponent {
    std::string type, value;
    bool operator==(const BenchComponent &) const = default;
};
struct BenchError { std::string code, message; };
struct BenchTemperatureRead { std::string sensor_id; uint64_t time_ns; double c; };
struct BenchAttempt {
    int child_id = 0;
    bool warmup = false;
    int slot = 0;
    uint64_t start_ns = 0, end_ns = 0;
    bool finite = false;
    std::vector<BenchComponent> checksum;
    int retry = 0;
    std::string status = "failed";
    double gate_wait_seconds = 0;
    std::optional<double> before, after, temperature_max, poll_gap_ms;
    std::optional<uint64_t> rss;
    std::vector<BenchTemperatureRead> reads;
    BenchError error;
};
struct BenchChild {
    int id = 0;
    std::optional<int> exit_code, signal;
    std::optional<uint64_t> rss;
    std::string stdout_path, stderr_path;
    bool logs_truncated = false;
};
struct BenchSummary { double median, mad, mad_percent, minimum, maximum; };
struct BenchRow {
    std::vector<BenchComponent> expected;
    std::vector<BenchAttempt> attempts;
    std::string key, label, size, configuration_id, isolation = "reuse", status = "pending", signature;
    int source_line = 0, accepted_warmups = 0, accepted_samples = 0, thermal_rejections = 0;
    std::optional<BenchSummary> summary;
    std::optional<double> temperature_max;
    std::optional<uint64_t> rss;
    std::string memory_reason;
    std::vector<BenchChild> children;
    BenchError error;
};
}
