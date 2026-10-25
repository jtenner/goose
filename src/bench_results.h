// Transport-independent records: thermal classification and structured reports
// can extend these without changing the one-release/one-call native boundary.
#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace goose {
struct BenchComponent {
    std::string type, value; // exact decimal / true,false / IEEE hex bits
    bool operator==(const BenchComponent &) const = default;
};
struct BenchAttempt {
    int child_id = 0;
    bool warmup = false;
    int slot = 0;
    uint64_t start_ns = 0, end_ns = 0;
    bool finite = false;
    std::vector<BenchComponent> checksum;
};
struct BenchRow {
    std::vector<BenchComponent> expected;
    std::vector<BenchAttempt> attempts;
};
}
