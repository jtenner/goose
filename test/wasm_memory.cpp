#include "../src/includes.h"
#include "../src/utils.h"
#include "../src/wasm_binary.h"
#include "../src/wasm_memory.h"

int main(int argc, char **argv) {
    using namespace goose;
    if (argc != 2 && argc != 3) return 2;
    WasmModule module;
    module.memories = argc == 3 ? (uint32_t)std::stoi(argv[2]) : 3;
    if (module.memories < 3 || module.memories > 65) return 2;
    auto fail = module.ImportFn("fail_v1", {WasmModule::I32, WasmModule::I32,
                                           WasmModule::I32, WasmModule::I32}, {});
    WasmMemoryRuntime runtime(module, fail);
    auto add = [&](const string &name, uint32_t fn) { module.exports.push_back({name, 0, fn}); };
    add("reserve1", runtime.Reserve(1));
    add("reserve2", runtime.Reserve(2));
    add("reserve", runtime.ReserveDynamic());
    add("top", runtime.Top(false));
    add("restore", runtime.Top(true));
    auto copy = runtime.CopyFromFrame();
    if (runtime.CopyFromFrame() != copy) return 1;
    add("copy_from_frame", copy);
    auto toframe = runtime.CopyToFrame();
    if (runtime.CopyToFrame() != toframe) return 1;
    add("copy_to_frame", toframe);
    auto paircopy = runtime.Copy();
    if (runtime.Copy() != paircopy) return 1;
    add("copy", paircopy);
    auto fill = runtime.Fill();
    if (runtime.Fill() != fill) return 1;
    add("fill", fill);
    auto prefix = runtime.ReadPrefix();
    if (runtime.ReadPrefix() != prefix) return 1;
    add("read_prefix", prefix);
    auto offsetload = runtime.Access(0x35, 4), hugeload = runtime.Access(0x35, 0x1000000);
    if (offsetload == runtime.Access(0x35) || hugeload == runtime.Access(0x35) ||
        offsetload != runtime.Access(0x35, 4)) return 1;
    add("load32off", offsetload);
    add("load32huge", hugeload);
    add("store32off", runtime.Access(0x3e, 4));
    for (auto [name, op] : vector<pair<string, uint8_t>> {
             {"load64", 0x29}, {"store64", 0x37}, {"load8s", 0x30}, {"load8u", 0x31},
             {"load16s", 0x32}, {"load16u", 0x33}, {"load32s", 0x34}, {"load32u", 0x35},
             {"store8", 0x3c}, {"store16", 0x3d}, {"store32", 0x3e},
             {"loadf32", 0x2a}, {"storef32", 0x38}, {"loadf64", 0x2b}, {"storef64", 0x39},
             {"loadbool", 0x2d}, {"storebool", 0x3a}}) {
        auto fn = runtime.Access(op);
        if (runtime.Access(op) != fn) return 1;
        add(name, fn);
    }
    for (uint32_t i = 0; i < module.memories; i++)
        module.exports.push_back({cat("memory", i), 2, i});
    auto data = module.Finish();
    auto file = fopen(argv[1], "wb");
    if (!file) return 1;
    auto wrote = fwrite(data.data(), 1, data.size(), file);
    auto closed = fclose(file);
    return wrote == data.size() && !closed ? 0 : 1;
}
