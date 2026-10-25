#include "../src/bench_report.h"
#include <cassert>
#include <cmath>
int main(int argc, char **argv) {
    using namespace goose;
    assert(argc == 2);
    assert(BenchHash("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    assert(BenchHash("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    auto s = BenchStatistics({1000000000,2000000000,3000000000,4000000000,100000000000});
    assert(s.median == 3 && s.mad == 1 && s.minimum == 1 && s.maximum == 100);
    s = BenchStatistics({1000000000,2000000000,6000000000,9000000000});
    assert(s.median == 4 && s.mad == 2.5 && s.mad_percent == 62.5);
    s = BenchStatistics({UINT64_MAX,UINT64_MAX-2});
    assert(std::isfinite(s.median) && s.mad == 1e-9);
    bool failed = false;
    try { BenchStatistics({0,1}); } catch (...) { failed = true; }
    assert(failed);
    BenchReport r;
    r.source_path = "/input.goose";r.source_hash=BenchHash("source");r.thermal.off=true;
    r.json_path=std::string(argv[1])+"/report.json";r.csv_path=std::string(argv[1])+"/report.csv";
    BenchConfiguration config;config.size="medium";config.definitions="[]";
    config.id=BenchConfigurationId(config,{{"/input.goose",r.source_hash}},BenchHash("compiler"),"");
    r.configurations.push_back(config);
    BenchRow row;row.key="entry";row.label="comma, quote\" newline\nUnicode λ";row.source_line=1;
    row.status="ok";row.size="medium";row.configuration_id=config.id;
    row.expected={{"u64","18446744073709551615"},{"f64","0x8000000000000000"},{"bool","true"}};
    row.summary=BenchStatistics({1000000000,2000000000,3000000000,4000000000,100000000000});
    row.accepted_samples=5;row.accepted_warmups=1;
    for(int i=0;i<6;++i){BenchAttempt a;a.warmup=i==0;a.slot=i==0?1:i;a.child_id=1;a.start_ns=123;a.end_ns=1000000123;a.status="accepted";a.checksum=row.expected;row.attempts.push_back(a);}
    row.children.push_back({1,0,{},4096,"/empty.stdout","/empty.stderr",false});row.rss=4096;
    r.rows.push_back(row);row.status="pending";row.summary.reset();row.expected.clear();row.attempts.clear();r.rows.push_back(row);
    r.Finish("ok");
}
