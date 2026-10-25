#include "../src/bench.cpp"
#include <cassert>
#include <cmath>
int main(int argc, char **argv) {
    using namespace goose;
    assert(argc == 2);
    auto decoded = DecodeAttempt("10 20 1 4096 i64:1;",1,false,1);
    assert(decoded.completed && decoded.rss == 4096 && decoded.end_ns-decoded.start_ns == 10);
    for (auto response : {"-10 20 1 4096 i64:1;", "10 20 3 4096 i64:1;", "10 20 1 4096 i64:1"}) {
        bool rejected=false;try{DecodeAttempt(response,1,false,1);}catch(...){rejected=true;}assert(rejected);
    }
    for (auto component : {BenchComponent{"u8","256"}, BenchComponent{"i64","01"}, BenchComponent{"bool","1"},
                           BenchComponent{"f64","0x7ff0000000000000"}, BenchComponent{"f64","0X0000000000000000"}}) {
        auto a=decoded;a.checksum={component};BenchRow row;
        bool rejected=false;try{BenchRecordAttempt(row,a,true);}catch(...){rejected=true;}assert(rejected);
    }
    double now=0;int reads=0;BenchThermalOptions options;
    BenchThermal fake {options,[&]{return ++reads<3?70.0:60.0;},[&]{return now;},[&](double delay){now+=delay;}};
    fake.gate();assert(now==2 && fake.waited==2 && fake.finish());
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
    BenchReport r; r.warmups=1; r.samples=5; r.warmups=1; r.samples=5;
    r.source_path = "/in\nput.goose";r.source_hash=BenchHash("source");r.thermal.off=true;
    r.json_path=std::string(argv[1])+"/report.json";r.csv_path=std::string(argv[1])+"/report.csv";
    BenchConfiguration config;config.size="medium";config.definitions=BenchArray({BenchObject({{"name",BenchString("TEST")},{"type",BenchString("string")},{"value",BenchString("\n\t\b\f\r")}})});
    config.id=BenchConfigurationId(config,{{r.source_path,r.source_hash}},BenchHash("compiler"),BenchHash("cc"));
    r.configurations.push_back(config);
    r.source_files={{r.source_path,r.source_hash}};
    r.goose=BenchObject({{"path",BenchString("/goose")},{"sha256",BenchString(BenchHash("compiler"))},{"version",BenchString("test")}});
    r.cc=BenchObject({{"path",BenchString("/cc")},{"sha256",BenchString(BenchHash("cc"))},{"version",BenchString("test")}});
    BenchRow row;row.key="entry";row.label="comma, quote\" newline\nUnicode λ";row.source_line=1;
    row.status="ok";row.size="medium";row.configuration_id=config.id;
    row.expected={{"u64","18446744073709551615"},{"f64","0x8000000000000000"},{"bool","true"}};
    row.summary=BenchStatistics({1000000000,2000000000,3000000000,4000000000,100000000000});
    row.accepted_samples=5;row.accepted_warmups=1;
    for(int i=0;i<6;++i){BenchAttempt a;a.warmup=i==0;a.slot=i==0?1:i;a.child_id=1;a.start_ns=123;a.end_ns=123+(i==0?9000000000ULL:i==5?100000000000ULL:(uint64_t)i*1000000000);a.status="accepted";a.completed=true;a.finite=true;a.checksum=row.expected;row.attempts.push_back(a);}
    row.children.push_back({1,0,{},4096,"/empty.stdout","/empty.stderr",false});row.rss=4096;
    r.rows.push_back(row);row.status="pending";row.summary.reset();row.expected.clear();row.attempts.clear();r.rows.push_back(row);
    // The same reducer as the supervisor, fed only recorded/fake call data.
    BenchRow recorded;
    for (int i=0;i<7;++i) {
        BenchAttempt a; a.completed=true;a.finite=true;a.warmup=i<2;a.start_ns=10;
        a.end_ns=10+(i==0 ? 999999999999ULL : i==1 ? 888888888888ULL : (uint64_t)(i-1)*1000000000);
        a.checksum={{"i64","7"}};
        BenchRecordAttempt(recorded,a,i!=1);recorded.attempts.push_back(a);
    }
    BenchCompleteRow(recorded,1,5);
    assert(recorded.summary->median==3 && recorded.thermal_rejections==1);
    auto bad=recorded.attempts.back();bad.checksum[0].value="8";
    failed=false;try{BenchRecordAttempt(recorded,bad,false);}catch(...){failed=true;}assert(failed);
    bad=recorded.attempts.back();bad.end_ns=bad.start_ns;
    failed=false;try{BenchRecordAttempt(recorded,bad,true);}catch(...){failed=true;}assert(failed);
    bad.end_ns=bad.start_ns-1;
    failed=false;try{BenchRecordAttempt(recorded,bad,true);}catch(...){failed=true;}assert(failed);
    recorded.accepted_samples=4;
    failed=false;try{BenchCompleteRow(recorded,1,5);}catch(...){failed=true;}assert(failed);
    r.Finish("ok");
    r.rows[1].status="failed";r.rows[1].error={"clock","nonpositive elapsed interval"};
    auto zero=decoded;zero.end_ns=zero.start_ns;zero.status="failed";zero.error=r.rows[1].error;
    auto negative=zero;negative.end_ns=negative.start_ns-1;
    BenchAttempt incomplete;incomplete.status="interrupted";incomplete.error={"interrupted","cancelled"};
    r.rows[1].attempts={zero,negative,incomplete};r.error=r.rows[1].error;
    r.json_path=std::string(argv[1])+"/partial.json";r.csv_path=std::string(argv[1])+"/partial.csv";
    r.Finish("failed");
    BenchReport unused;unused.thermal.gate=std::nan("");unused.Checkpoint();
    unused.csv_path=std::string(argv[1])+"/unused.csv";unused.Checkpoint();

}
