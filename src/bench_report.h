#pragma once
#include "bench_results.h"
#include "bench_thermal.h"
#include <utility>
#include <iosfwd>
namespace goose {
using BenchFields = std::vector<std::pair<std::string, std::string>>;
std::string BenchString(const std::string &s);
std::string BenchNumber(double n);
std::string BenchObject(const BenchFields &fields);
std::string BenchArray(const std::vector<std::string> &values);
std::string BenchStrings(const std::vector<std::string> &values);
std::string BenchChecksum(const std::vector<BenchComponent> &components);
std::string BenchHash(const std::string &bytes);
std::string BenchFileHash(const std::string &path);
std::string BenchReadFile(const std::string &path);
std::string BenchTimestamp();
std::string BenchUUID();
std::string BenchHost();
BenchSummary BenchStatistics(const std::vector<uint64_t> &nanoseconds);
void BenchRecordAttempt(BenchRow &, BenchAttempt &, bool accepted);
void BenchCompleteRow(BenchRow &, int warmups, int samples);
struct BenchConfiguration {
    std::string id, size, definitions;
    std::vector<std::string> goose_flags, native_flags;
    std::string executable_hash, c_hash;
};
struct BenchReport {
    std::string run_id = BenchUUID(), started_at = BenchTimestamp(), finished_at, status = "running";
    std::string source_path, source_hash, git_commit, git_dirty = "null";
    BenchFields source_files; // absolute path, SHA-256
    std::string host = BenchHost(), goose = "null", cc = "null";
    std::vector<BenchConfiguration> configurations;
    BenchThermalOptions thermal;
    std::vector<std::string> sensors; // serialized sensor descriptors
    std::string thermal_reason;
    bool fresh = false;
    int warmups = 2, samples = 7;
    std::vector<BenchRow> rows;
    BenchError error;
    std::string json_path, csv_path;
    std::string Json() const;
    void WriteJson(std::ostream &) const;
    void Checkpoint(bool csv = false) const;
    void Print() const;
    void Finish(const std::string &state);
};
std::string BenchConfigurationId(const BenchConfiguration &, const BenchFields &sources,
                                 const std::string &goose_hash, const std::string &cc_hash);
}
