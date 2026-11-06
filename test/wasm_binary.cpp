// Independent engine validation consumes this test's emitted binary.
#include "../src/includes.h"
#include "../src/utils.h"
#include "../src/wasm_binary.h"
#ifdef __linux__
#include <sys/mman.h>
#include <sys/resource.h>
#endif

int main(int argc, char **argv) {
    using namespace goose;
    if (argc != 2) return 2;
    if (string_view(argv[1]) == "overflow") {
#ifdef __linux__
        // A valid span, backed by a lazy virtual mapping. Limit the process's
        // address space so a broken encoder cannot copy this entire span.
        auto size = (uint64_t)UINT32_MAX + 1;
        auto region = mmap(nullptr, (size_t)size, PROT_READ, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (region == MAP_FAILED) return 77;
        rlimit limit {6ull << 30, 6ull << 30};
        if (setrlimit(RLIMIT_AS, &limit)) { munmap(region, (size_t)size); return 77; }
        bool rejected = false;
        try {
            WasmModule m;
            m.Data(string_view((const char *)region, (size_t)size));
        } catch (const CompileError &e) {
            rejected = e.msg.find("static data exceeds memory32") != string::npos;
        } catch (const std::bad_alloc &) {
            fprintf(stderr, "encoder attempted an allocation for an invalid Memory32 size\n");
        }
        munmap(region, (size_t)size);
        return rejected ? 0 : 1;
#else
        return 77;
#endif
    }
    {
        WasmBytes b;
        bool rejected = false;
        try { b.U(1ull << 32); }
        catch (const CompileError &e) { rejected = e.msg.find("u32") != string::npos; }
        if (!rejected) { fprintf(stderr, "encoder accepted an out-of-range unsigned module field\n"); return 1; }
        b.bytes.clear(); b.U(UINT32_MAX);
        if (b.bytes != string("\xff\xff\xff\xff\x0f", 5)) return 1;
        b.bytes.clear(); b.Mem(0x29, 129, 300);
        if (b.bytes != string("\x29\x40\x81\x01\xac\x02", 6)) return 1;
        b.bytes.clear(); b.Mem(0x29, 0, 300);
        if (b.bytes != string("\x29\x00\xac\x02", 4)) return 1;
    }
    WasmModule m;
    m.memories = 2;
    vector<int64_t> values {0, 63, 64, 127, 128, -64, -65, -128, -129, INT64_MIN, INT64_MAX};
    for (size_t i = 0; i < values.size(); i++) {
        auto fn = m.AddFn(cat("constant", i), {}, {WasmModule::I64});
        m.functions.back().code.I64(values[i]);
        m.exports.push_back({cat("constant", i), 0, fn});
    }
    auto fn = m.AddFn("unaligned.memory1", {}, {WasmModule::I64});
    auto &code = m.functions.back().code;
    code.I32(1); code.I64(INT64_MIN); code.Mem(0x37, 1);
    code.I32(1); code.Mem(0x29, 1);
    m.exports.push_back({"unaligned", 0, fn});
    m.exports.push_back({"memory", 2, 0});
    m.exports.push_back({"other", 2, 1});
    auto data = m.Finish();
    auto f = fopen(argv[1], "wb");
    if (!f) return 1;
    auto wrote = fwrite(data.data(), 1, data.size(), f);
    auto closed = fclose(f);
    return wrote == data.size() && !closed ? 0 : 1;
}
