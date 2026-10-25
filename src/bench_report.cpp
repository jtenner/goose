#include "bench_report.h"
#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <limits>
#include <random>
#include <sstream>
#include <functional>
#include <stdexcept>
#ifdef __linux__
#include <sched.h>
#include <sys/utsname.h>
#include <unistd.h>
#endif
namespace goose {
using std::string; using std::vector; using std::to_string;
string BenchString(const string &s) {
    string out = "\"";
    constexpr char hex[] = "0123456789abcdef";
    for (unsigned char c : s) {
        if (c == '"' || c == '\\') { out += '\\'; out += c; }
        else if (c == '\b') out += "\\b";
        else if (c == '\f') out += "\\f";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += c;
    }
    return out + '"';
}
string BenchNumber(double n) {
    if (!std::isfinite(n)) throw std::runtime_error("nonfinite report number");
    char b[64];
    auto result = std::to_chars(b, b + sizeof b, n, std::chars_format::general, 17);
    if (result.ec != std::errc()) throw std::runtime_error("cannot encode report number");
    return string(b, result.ptr);
}
string BenchObject(const BenchFields &fields) {
    string s = "{";
    for (auto &[k,v] : fields) { if (s.size() > 1) s += ','; s += BenchString(k) + ':' + v; }
    return s + '}';
}
string BenchArray(const vector<string> &values) {
    string s = "[";
    for (auto &v : values) { if (s.size() > 1) s += ','; s += v; }
    return s + ']';
}
string BenchStrings(const vector<string> &values) {
    vector<string> a; for (auto &v : values) a.push_back(BenchString(v)); return BenchArray(a);
}
string BenchChecksum(const vector<BenchComponent> &components) {
    if (components.empty()) return "null";
    vector<string> values;
    for (auto &c : components) values.push_back(BenchObject({{"type", BenchString(c.type)},
        {"value", (c.type == "bool" && (c.value == "true" || c.value == "false")) ? c.value : BenchString(c.value)}}));
    return BenchObject({{"components", BenchArray(values)}});
}
namespace {
// FIPS 180-4 SHA-256. Streaming blocks keep binary provenance memory bounded.
struct Sha256 {
    uint32_t h[8] {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    unsigned char buffer[64] {}; size_t used = 0; uint64_t length = 0;
    void block(const unsigned char *b) {
        static constexpr uint32_t k[64] {
            0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
            0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
            0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
            0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
            0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
            0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
            0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
            0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
        uint32_t w[64];
        for (int i=0;i<16;++i) w[i]=(uint32_t(b[4*i])<<24)|(uint32_t(b[4*i+1])<<16)|(uint32_t(b[4*i+2])<<8)|b[4*i+3];
        for (int i=16;i<64;++i) w[i]=w[i-16]+(std::rotr(w[i-15],7)^std::rotr(w[i-15],18)^(w[i-15]>>3))+w[i-7]+(std::rotr(w[i-2],17)^std::rotr(w[i-2],19)^(w[i-2]>>10));
        auto a=h[0],b0=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],h0=h[7];
        for(int i=0;i<64;++i) {
            auto t1=h0+(std::rotr(e,6)^std::rotr(e,11)^std::rotr(e,25))+((e&f)^(~e&g))+k[i]+w[i];
            auto t2=(std::rotr(a,2)^std::rotr(a,13)^std::rotr(a,22))+((a&b0)^(a&c)^(b0&c));
            h0=g;g=f;f=e;e=d+t1;d=c;c=b0;b0=a;a=t1+t2;
        }
        h[0]+=a;h[1]+=b0;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=h0;
    }
    void add(const char *p, size_t n) {
        length += n;
        while(n) { auto take=std::min(n,64-used); memcpy(buffer+used,p,take); used+=take;p+=take;n-=take;
            if(used==64) { block(buffer);used=0; } }
    }
    string finish() {
        auto bits=length*8; buffer[used++]=0x80;
        if(used>56) { memset(buffer+used,0,64-used);block(buffer);used=0; }
        memset(buffer+used,0,56-used);
        for(int i=0;i<8;++i) buffer[63-i]=(unsigned char)(bits>>(8*i));
        block(buffer); string s;
        for(auto v:h) { char b[9];snprintf(b,sizeof b,"%08x",v);s+=b; } return s;
    }
};
string ErrorJson(const BenchError &e) { return e.code.empty() ? "null" : BenchObject({{"code",BenchString(e.code)},{"message",BenchString(e.message)}}); }
template<class T> string Optional(const std::optional<T> &v) { return v ? to_string(*v) : "null"; }
string Optional(const std::optional<double> &v) { return v ? BenchNumber(*v) : "null"; }
string Nullable(const string &s) { return s.empty() ? "null" : BenchString(s); }
string SummaryJson(const std::optional<BenchSummary> &s) {
    if (!s) return "null";
    return BenchObject({{"median_seconds",BenchNumber(s->median)},{"seconds_mad",BenchNumber(s->mad)},
        {"seconds_mad_percent",BenchNumber(s->mad_percent)},{"seconds_min",BenchNumber(s->minimum)},{"seconds_max",BenchNumber(s->maximum)}});
}
string AttemptJson(const BenchAttempt &a, int index) {
    vector<string> reads;
    for (auto &r : a.reads) {
        // Avoid unsigned subtraction and signed overflow for negative offsets.
        auto offset = r.time_ns >= a.start_ns ? to_string(r.time_ns-a.start_ns) : "-"+to_string(a.start_ns-r.time_ns);
        reads.push_back(BenchObject({{"sensor_id",BenchString(r.sensor_id)},{"offset_ns",BenchString(offset)},{"c",BenchNumber(r.c)}}));
    }
    bool complete = a.completed;
    return BenchObject({{"index",to_string(index)},{"phase",BenchString(a.warmup?"warmup":"measure")},{"slot",to_string(a.slot)},
        {"retry",to_string(a.retry)},{"child_id",to_string(a.child_id)},{"status",BenchString(a.status)},
        {"elapsed_ns",complete?BenchString(a.end_ns >= a.start_ns ? to_string(a.end_ns-a.start_ns) : "-"+to_string(a.start_ns-a.end_ns)):"null"},
        {"seconds",complete?BenchNumber(double((long double)a.end_ns-(long double)a.start_ns)/1e9):"null"},{"checksum",BenchChecksum(a.checksum)},
        {"gate_wait_seconds",BenchNumber(a.gate_wait_seconds)},{"temperature_before_c",Optional(a.before)},
        {"temperature_after_c",Optional(a.after)},{"temperature_max_observed_c",Optional(a.temperature_max)},
        {"temperature_reads",BenchArray(reads)},{"temperature_max_poll_gap_ms",Optional(a.poll_gap_ms)},
        {"process_peak_rss_bytes",Optional(a.rss)},{"error",ErrorJson(a.error)}});
}
void AtomicWrite(const string &path, const std::function<void(std::ostream &)> &write, const string &id) {
    if (path.empty()) return;
    auto temporary = path + ".tmp-" + id;
    try {
        std::ofstream f(temporary, std::ios::binary | std::ios::trunc);
        if (!f) throw std::runtime_error("cannot write artifact: " + path);
        write(f);
        if (!f.flush()) throw std::runtime_error("cannot write artifact: " + path);
        f.close(); if (!f) throw std::runtime_error("cannot close artifact: " + path);
        std::filesystem::rename(temporary,path);
    } catch (...) { std::error_code ec; std::filesystem::remove(temporary,ec); throw; }
}
void AtomicWrite(const string &path, const string &text, const string &id) {
    AtomicWrite(path,[&](std::ostream &out) { out.write(text.data(),text.size()); },id);
}
string Csv(const vector<string> &cells) {
    string s;
    for (auto &v : cells) {
        if (!s.empty()) s+=',';
        s+='"'; for(char c:v) { if(c=='"') s+='"';s+=c; } s+='"';
    }
    return s+"\r\n";
}
string Cell(const string &s) { return s=="null"?"":s; }
string Safe(const string &s) {
    string result;
    for(size_t i=0;i<s.size();++i) {
        auto c=(unsigned char)s[i];
        if(c<32 || c==127 || (c==0xc2 && i+1<s.size() && (unsigned char)s[i+1]>=128 && (unsigned char)s[i+1]<=159)) {
            if(c==0xc2)c=(unsigned char)s[++i];
            char b[8];snprintf(b,sizeof b,"\\u%04x",c);result+=b;
        } else result+=c;
    }
    return result;
}
}
string BenchReadFile(const string &path) {
    std::ifstream f(path,std::ios::binary); if(!f) throw std::runtime_error("cannot read provenance input: "+path);
    string s((std::istreambuf_iterator<char>(f)),{}); if(f.bad()) throw std::runtime_error("cannot read provenance input: "+path);return s;
}
string BenchHash(const string &bytes) { Sha256 h;h.add(bytes.data(),bytes.size());return h.finish(); }
string BenchFileHash(const string &path) {
    std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("cannot hash provenance input: "+path);
    Sha256 h; char b[65536];while(f) { f.read(b,sizeof b);h.add(b,(size_t)f.gcount()); }
    if(f.bad())throw std::runtime_error("cannot hash provenance input: "+path);
    return h.finish();
}
string BenchTimestamp() {
    auto now=std::time(nullptr);std::tm tm{};
#ifdef _WIN32
    gmtime_s(&tm,&now);
#else
    gmtime_r(&now,&tm);
#endif
    char b[32];std::strftime(b,sizeof b,"%Y-%m-%dT%H:%M:%SZ",&tm);return b;
}
string BenchUUID() {
    std::random_device random; unsigned char bytes[16]; for(auto &b:bytes)b=(unsigned char)random();
    bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
    string s;for(int i=0;i<16;++i) { if(i==4||i==6||i==8||i==10)s+='-';char b[3];snprintf(b,sizeof b,"%02x",bytes[i]);s+=b; }return s;
}
string BenchHost() {
    string os="unknown",kernel="unknown",arch="unknown",cpu="unknown",resolution="0",affinity="null",memory="unavailable";int cpus=0;
#ifdef __linux__
    utsname u{};if(!uname(&u)){os=u.sysname;kernel=u.release;arch=u.machine;}
    cpus=(int)sysconf(_SC_NPROCESSORS_ONLN); if(cpus<0)cpus=0;
    // Dynamic affinity masks support hosts with more than CPU_SETSIZE CPUs.
    auto count=std::max(128L,sysconf(_SC_NPROCESSORS_CONF));
    for(int tries=0;tries<8;++tries,count*=2) {
        auto set=CPU_ALLOC(count);if(!set)break;auto size=CPU_ALLOC_SIZE(count);CPU_ZERO_S(size,set);
        bool ok=sched_getaffinity(0,size,set)==0;vector<string> ids;
        if(ok)for(int i=0;i<count;++i)if(CPU_ISSET_S(i,size,set))ids.push_back(to_string(i));
        CPU_FREE(set);if(ok){affinity=BenchArray(ids);break;}
    }
    std::ifstream f("/proc/cpuinfo");string line;
    while(std::getline(f,line))if(line.starts_with("model name")){auto p=line.find(':');if(p!=string::npos)cpu=line.substr(p+2);break;}
    timespec r{};if(!clock_getres(CLOCK_MONOTONIC,&r))resolution=to_string(uint64_t(r.tv_sec)*1000000000+r.tv_nsec);
    memory="linux_process_peak_rss";
#endif
    return BenchObject({{"os",BenchString(os)},{"kernel",BenchString(kernel)},{"architecture",BenchString(arch)},
        {"cpu_model",BenchString(cpu)},{"logical_cpus",to_string(cpus)},{"affinity",affinity},
        {"clock",BenchString("CLOCK_MONOTONIC")},{"clock_resolution_ns",BenchString(resolution)},{"memory_metric",BenchString(memory)}});
}
BenchSummary BenchStatistics(const vector<uint64_t> &nanoseconds) {
    if(nanoseconds.empty())throw std::runtime_error("no accepted measured durations");
    vector<long double> x; for(auto n:nanoseconds){if(!n)throw std::runtime_error("nonpositive elapsed interval (clock resolution)");x.push_back(n);}
    auto median=[](vector<long double> &v){std::sort(v.begin(),v.end());auto n=v.size();return n%2?v[n/2]:(v[n/2-1]/2+v[n/2]/2);};
    auto m=median(x),lo=x.front(),hi=x.back(); for(auto &v:x)v=std::abs(v-m);auto mad=median(x);
    return {double(m/1e9L),double(mad/1e9L),double(100*mad/m),double(lo/1e9L),double(hi/1e9L)};
}
namespace {
void ValidateChecksum(const vector<BenchComponent> &components) {
    for (auto &c:components) {
        if (c.type == "bool") {
            if (c.value != "true" && c.value != "false") throw std::runtime_error("invalid boolean checksum protocol");
        } else if (c.type == "f32" || c.type == "f64") {
            auto width = c.type == "f32" ? 8u : 16u;
            if (c.value.size() != width+2 || !c.value.starts_with("0x") || c.value.find_first_not_of("0123456789abcdef",2) != string::npos)
                throw std::runtime_error("invalid floating checksum protocol");
            uint64_t bits = 0;
            auto parsed = std::from_chars(c.value.data()+2,c.value.data()+c.value.size(),bits,16);
            if (parsed.ec != std::errc()) throw std::runtime_error("invalid floating checksum protocol");
            bool finite = width == 8 ? std::isfinite(std::bit_cast<float>((uint32_t)bits)) : std::isfinite(std::bit_cast<double>(bits));
            if (!finite) throw std::runtime_error("nonfinite benchmark checksum");
        } else {
            int width = c.type == "i8" || c.type == "u8" ? 8 : c.type == "i16" || c.type == "u16" ? 16 :
                c.type == "i32" || c.type == "u32" ? 32 : c.type == "i64" || c.type == "u64" ? 64 : 0;
            if (!width) throw std::runtime_error("unknown checksum type protocol");
            auto first=c.value.data(),end=first+c.value.size();
            if (c.type[0]=='u') {
                uint64_t value=0;auto parsed=std::from_chars(first,end,value);
                if(parsed.ec!=std::errc() || parsed.ptr!=end || to_string(value)!=c.value || (width<64 && value>=(uint64_t(1)<<width)))
                    throw std::runtime_error("invalid unsigned checksum protocol");
            } else {
                int64_t value=0;auto parsed=std::from_chars(first,end,value);
                if(parsed.ec!=std::errc() || parsed.ptr!=end || to_string(value)!=c.value ||
                    (width<64 && (value<-(int64_t(1)<<(width-1)) || value>=(int64_t(1)<<(width-1)))))
                    throw std::runtime_error("invalid signed checksum protocol");
            }
        }
    }
}
}
void BenchRecordAttempt(BenchRow &row, BenchAttempt &a, bool accepted) {
    if (a.temperature_max) row.temperature_max = std::max(row.temperature_max.value_or(*a.temperature_max), *a.temperature_max);
    if (!a.completed || a.end_ns <= a.start_ns) throw std::runtime_error("nonpositive elapsed interval (clock resolution)");
    if (!a.finite) throw std::runtime_error("nonfinite benchmark checksum");
    if (a.checksum.empty()) throw std::runtime_error("missing benchmark checksum protocol");
    ValidateChecksum(a.checksum);
    if (row.expected.empty()) row.expected = a.checksum;
    else if (row.expected != a.checksum) throw std::runtime_error("checksum disagreement for " + row.key + " (" + row.size + ")");
    a.status = accepted ? "accepted" : "thermal_rejected";
    if (accepted) { if (a.warmup) ++row.accepted_warmups; else ++row.accepted_samples; }
    else ++row.thermal_rejections;
}
void BenchCompleteRow(BenchRow &row, int warmups, int samples) {
    if (row.accepted_warmups != warmups || row.accepted_samples != samples || warmups < 1 || samples < 5)
        throw std::runtime_error("incomplete benchmark row");
    for (auto &c: row.children) if (!c.exit_code || *c.exit_code != 0 || c.signal)
        throw std::runtime_error("benchmark child failed during teardown");
    vector<uint64_t> accepted;
    for (auto &a:row.attempts) if (!a.warmup && a.status == "accepted") accepted.push_back(a.end_ns-a.start_ns);
    if ((int)accepted.size() != samples) throw std::runtime_error("incomplete benchmark attempts");
    row.summary = BenchStatistics(accepted); row.status = "ok";
}
string BenchConfigurationId(const BenchConfiguration &c,const BenchFields &sources,const string &goose_hash,const string &cc_hash) {
    auto sorted=sources;std::sort(sorted.begin(),sorted.end());vector<string> files;
    for(auto &[path,hash]:sorted)files.push_back(BenchObject({{"path",BenchString(path)},{"sha256",BenchString(hash)}}));
    // Recursive key order is lexical, including definitions (name,type,value).
    return BenchHash(BenchObject({{"cc_sha256",Nullable(cc_hash)},{"definitions",c.definitions},{"goose_flags",BenchStrings(c.goose_flags)},
        {"goose_sha256",BenchString(goose_hash)},{"native_flags",BenchStrings(c.native_flags)},{"size",BenchString(c.size)},{"source_files",BenchArray(files)}}));
}
string BenchReport::Json() const {
    std::ostringstream out;WriteJson(out);return out.str();
}
void BenchReport::WriteJson(std::ostream &out) const {
    vector<string> files, configs;
    for(auto &[path,hash]:source_files)files.push_back(BenchObject({{"path",BenchString(path)},{"sha256",BenchString(hash)}}));
    for(auto &c:configurations)configs.push_back(BenchObject({{"id",BenchString(c.id)},{"size",BenchString(c.size)},{"definitions",c.definitions},
        {"goose_flags",BenchStrings(c.goose_flags)},{"native_flags",BenchStrings(c.native_flags)},
        {"executable_sha256",Nullable(c.executable_hash)},{"generated_c_sha256",Nullable(c.c_hash)}}));
    auto prefix = BenchObject({{"schema_version","1"},{"run_id",BenchString(run_id)},{"status",BenchString(status)},
        {"started_at",BenchString(started_at)},{"finished_at",Nullable(finished_at)},
        {"source",BenchObject({{"path",BenchString(source_path)},{"sha256",BenchString(source_hash)},{"files",BenchArray(files)},
            {"git_commit",Nullable(git_commit)},{"git_dirty",git_dirty}})}, {"host",host},{"toolchain",BenchObject({{"goose",goose},{"cc",cc}})},
        {"configurations",BenchArray(configs)},{"policy",BenchObject({{"samples",to_string(samples)},{"warmups",to_string(warmups)},
            {"isolation",BenchString(fresh?"process":"reuse")},{"setup_timeout_seconds",BenchNumber(thermal.setup_timeout)},
            {"sample_timeout_seconds",BenchNumber(thermal.sample_timeout)},{"gate_timeout_seconds",BenchNumber(thermal.gate_timeout)},
            {"max_retries",to_string(thermal.retries)},{"thermal",BenchObject({{"mode",BenchString(thermal.off?"disabled":"required")},
                {"reason",Nullable(thermal_reason)},{"gate_c",BenchNumber(thermal.gate)},{"ceiling_c",BenchNumber(thermal.ceiling)},
                {"poll_interval_ms",BenchNumber(thermal.poll_ms)},{"sensors",BenchArray(sensors)}})}})},
        {"error",ErrorJson(error)}});
    prefix.pop_back();out << prefix << ",\"results\":[";
    bool first=true;
    for(auto &r:rows) {
        if(!first)out << ',';
        first=false;
        auto row = BenchObject({{"key",BenchString(r.key)},{"label",BenchString(r.label)},{"source_line",to_string(r.source_line)},
            {"size",BenchString(r.size)},{"configuration_id",BenchString(r.configuration_id)},{"status",BenchString(r.status)},{"isolation",BenchString(r.isolation)},
            {"checksum",BenchChecksum(r.expected)},{"accepted_warmups",to_string(r.accepted_warmups)},{"accepted_samples",to_string(r.accepted_samples)},
            {"thermal_rejections",to_string(r.thermal_rejections)},{"summary",SummaryJson(r.summary)},
            {"temperature_max_observed_c",Optional(r.temperature_max)},{"process_peak_rss_bytes",Optional(r.rss)},
            {"memory_unavailable_reason",Nullable(r.memory_reason)},{"error",ErrorJson(r.error)}});
        row.pop_back();out << row << ",\"attempts\":[";
        int index=0;for(auto &a:r.attempts) { if(index)out << ',';out << AttemptJson(a,++index); }
        out << "],\"children\":[";
        bool firstchild=true;
        for(auto &c:r.children) {
            if(!firstchild)out << ',';
            firstchild=false;
            out << BenchObject({{"id",to_string(c.id)},{"exit_code",Optional(c.exit_code)},{"signal",Optional(c.signal)},
                {"process_peak_rss_bytes",Optional(c.rss)},{"stdout_path",BenchString(c.stdout_path)},{"stderr_path",BenchString(c.stderr_path)},{"logs_truncated",c.logs_truncated?"true":"false"}});
        }
        out << "]}";
    }
    out << "]}\n";
}
void BenchReport::Checkpoint(bool csv) const {
    if (!json_path.empty()) AtomicWrite(json_path,[&](std::ostream &out) { WriteJson(out); },run_id);
    if(!csv||csv_path.empty())return;
    string summary="schema_version,run_id,key,label,source_path,source_sha256,source_line,size,configuration_id,isolation,status,thermal_mode,gate_c,ceiling_c,warmups_requested,samples_requested,accepted_warmups,accepted_samples,thermal_rejections,median_seconds,seconds_mad,seconds_mad_percent,seconds_min,seconds_max,temperature_max_observed_c,process_peak_rss_bytes,memory_unavailable_reason,checksum_json,error_code,error_message\r\n";
    string raw="schema_version,run_id,key,size,configuration_id,index,phase,slot,retry,child_id,status,elapsed_ns,seconds,gate_wait_seconds,temperature_before_c,temperature_after_c,temperature_max_observed_c,temperature_max_poll_gap_ms,process_peak_rss_bytes,checksum_json,error_code,error_message\r\n";
    for(auto &r:rows) {
        auto e=r.error.code.empty()&&r.status=="pending"?error:r.error;
        summary+=Csv({"1",run_id,r.key,r.label,source_path,source_hash,to_string(r.source_line),r.size,r.configuration_id,r.isolation,r.status,
            thermal.off?"disabled":"required",BenchNumber(thermal.gate),BenchNumber(thermal.ceiling),to_string(warmups),to_string(samples),
            to_string(r.accepted_warmups),to_string(r.accepted_samples),to_string(r.thermal_rejections),
            r.summary?BenchNumber(r.summary->median):"",r.summary?BenchNumber(r.summary->mad):"",r.summary?BenchNumber(r.summary->mad_percent):"",
            r.summary?BenchNumber(r.summary->minimum):"",r.summary?BenchNumber(r.summary->maximum):"",Cell(Optional(r.temperature_max)),Cell(Optional(r.rss)),
            r.memory_reason,Cell(BenchChecksum(r.expected)),e.code,e.message});
        int i=0;for(auto &a:r.attempts) {
            bool complete=a.completed;
            raw+=Csv({"1",run_id,r.key,r.size,r.configuration_id,to_string(++i),a.warmup?"warmup":"measure",to_string(a.slot),to_string(a.retry),
                to_string(a.child_id),a.status,complete?(a.end_ns >= a.start_ns ? to_string(a.end_ns-a.start_ns) : "-"+to_string(a.start_ns-a.end_ns)):"",complete?BenchNumber(double((long double)a.end_ns-(long double)a.start_ns)/1e9):"",
                BenchNumber(a.gate_wait_seconds),Cell(Optional(a.before)),Cell(Optional(a.after)),Cell(Optional(a.temperature_max)),Cell(Optional(a.poll_gap_ms)),
                Cell(Optional(a.rss)),Cell(BenchChecksum(a.checksum)),a.error.code,a.error.message});
        }
    }
    auto path=std::filesystem::path(csv_path);auto ext=path.extension().string();path.replace_extension();
    auto samples_path=path.string()+".samples"+ext;
    AtomicWrite(csv_path,summary,run_id);AtomicWrite(samples_path,raw,run_id);
}
void BenchReport::Finish(const string &state) { status=state;finished_at=BenchTimestamp();Checkpoint(true); }
void BenchReport::Print() const {
    printf("Benchmark source: %s\nGoose/toolchain: %s / %s\n",Safe(source_path).c_str(),Safe(goose).c_str(),Safe(cc).c_str());
    printf("Warmups: %d; gate: %g C; ceiling: %g C%s\n",warmups,thermal.gate,thermal.ceiling,thermal.off?"; UNGATED":"");
    for(auto &c:configurations)printf("Configuration %s %s: Goose %s; native %s\n",c.size.c_str(),c.id.c_str(),Safe(BenchStrings(c.goose_flags)).c_str(),Safe(BenchStrings(c.native_flags)).c_str());
    puts("key\tlabel\tsize\tisolation\tcount\tmedian ms\tMAD %\tmin ms\tmax ms\tmax observed Tctl C\trejections\tprocess peak MiB\tchecksum\tstatus\tsignature");
    auto number=[](std::optional<double> v){return v?BenchNumber(*v):"n/a";};
    for(auto &r:rows) {
        auto s=r.summary;
        printf("%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\n",Safe(r.key).c_str(),Safe(r.label).c_str(),r.size.c_str(),r.isolation.c_str(),r.accepted_samples,
            number(s?std::optional(s->median*1000):std::nullopt).c_str(),number(s?std::optional(s->mad_percent):std::nullopt).c_str(),
            number(s?std::optional(s->minimum*1000):std::nullopt).c_str(),number(s?std::optional(s->maximum*1000):std::nullopt).c_str(),
            number(r.temperature_max).c_str(),r.thermal_rejections,number(r.rss?std::optional(double(*r.rss)/1048576):std::nullopt).c_str(),
            Safe(r.expected.empty() ? "n/a" : BenchChecksum(r.expected)).c_str(),r.status.c_str(),Safe(r.signature).c_str());
    }
    puts("RSS is the process lifetime high-water mark, including runtime and global fixtures.");
}
}
