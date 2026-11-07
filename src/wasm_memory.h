// Memory32 data-stack helpers. Each logical stack has a distinct physical
// memory and top. Packed addresses use high u32 memory / low u32 offset.
#pragma once

namespace goose {

struct WasmMemoryRuntime {
    WasmModule &module;
    uint32_t failure;
    unordered_map<uint32_t, uint32_t> reserves, accesses;
    uint32_t dynamicreserve = UINT32_MAX, gettop = UINT32_MAX, settop = UINT32_MAX;

    WasmMemoryRuntime(WasmModule &m, uint32_t fail) : module(m), failure(fail) {}

    void Trap(WasmBytes &c, int error) {
        c.I32(error); c.I32(0); c.I32(0); c.I32(0); c.Call(failure); c.Byte(0x00);
    }
    void Save(uint32_t fn, WasmBytes code, vector<uint8_t> locals = {}) {
        auto &f = module.functions[fn - module.imports.size()];
        f.code = std::move(code); f.locals = std::move(locals);
    }

    // Selector 0 enters the first case. Each case branches to the shared
    // result block. The default exits all case blocks and reports an invalid
    // memory identity, including negative selectors interpreted as u32.
    template<class Select, class Case>
    void Dispatch(WasmBytes &c, uint32_t first, uint8_t result, Select select, Case emit) {
        auto count = module.memories - first;
        c.Byte(0x02); c.Byte(result);
        c.Byte(0x02); c.Byte(0x40);
        for (uint32_t i = 0; i < count; i++) { c.Byte(0x02); c.Byte(0x40); }
        select(); c.Byte(0x0e); c.U(count);
        for (uint32_t i = 0; i < count; i++) c.U(i);
        c.U(count);
        for (uint32_t i = 0; i < count; i++) {
            c.Byte(0x0b); emit(first + i);
            c.Byte(0x0c); c.U(count - i);
        }
        c.Byte(0x0b); Trap(c, 7); c.Byte(0x0b);
    }

    uint32_t Reserve(uint32_t memory) {
        if (memory >= module.memories) throw CompileError {"wasm: invalid reserve memory"};
        if (auto it = reserves.find(memory); it != reserves.end()) return it->second;
        auto fn = module.AddFn(cat("goose.reserve_memory.", memory), {WasmModule::I32}, {WasmModule::I32});
        reserves[memory] = fn;
        WasmBytes c;
        // Parameters: byte count. Locals: old i32, exclusive end i64, pages i32.
        c.Byte(0x23); c.U(memory); c.Tee(1); c.Byte(0xad);
        c.Get(0); c.Byte(0xad); c.Byte(0x7c); c.Tee(2);
        c.I64(UINT32_MAX); c.Byte(0x56); c.Byte(0x04); c.Byte(0x40);
        Trap(c, 6); c.Byte(0x0b);
        c.Get(2); c.I64(65535); c.Byte(0x7c); c.I64(16); c.Byte(0x88); c.Byte(0xa7); c.Tee(3);
        c.Byte(0x3f); c.U(memory); c.Byte(0x4b); c.Byte(0x04); c.Byte(0x40);
        c.Get(3); c.Byte(0x3f); c.U(memory); c.Byte(0x6b);
        c.Byte(0x40); c.U(memory); c.I32(-1); c.Byte(0x46); c.Byte(0x04); c.Byte(0x40);
        Trap(c, 6); c.Byte(0x0b); c.Byte(0x0b);
        // Publish the new top only after growth succeeds.
        c.Get(2); c.Byte(0xa7); c.Byte(0x24); c.U(memory); c.Get(1);
        Save(fn, std::move(c), {WasmModule::I32, WasmModule::I64, WasmModule::I32});
        return fn;
    }

    uint32_t ReserveDynamic() {
        if (dynamicreserve != UINT32_MAX) return dynamicreserve;
        auto fn = module.AddFn("goose.reserve_data", {WasmModule::I32, WasmModule::I32}, {WasmModule::I32});
        dynamicreserve = fn;
        WasmBytes c;
        Dispatch(c, 1, WasmModule::I32,
                 [&] { c.Get(0); c.I32(1); c.Byte(0x6b); },
                 [&](uint32_t memory) { c.Get(1); c.Call(Reserve(memory)); });
        Save(fn, std::move(c));
        return fn;
    }

    uint32_t Top(bool write) {
        auto &cached = write ? settop : gettop;
        if (cached != UINT32_MAX) return cached;
        auto params = vector<uint8_t> {WasmModule::I32};
        if (write) params.push_back(WasmModule::I32);
        auto fn = module.AddFn(write ? "goose.restore_data" : "goose.data_top", params,
                               write ? vector<uint8_t> {} : vector<uint8_t> {WasmModule::I32});
        cached = fn;
        WasmBytes c;
        Dispatch(c, 1, write ? 0x40 : WasmModule::I32,
                 [&] { c.Get(0); c.I32(1); c.Byte(0x6b); }, [&](uint32_t memory) {
            if (write) {
                c.Get(1); c.Byte(0x45); c.Byte(0x04); c.Byte(0x40); Trap(c, 7); c.Byte(0x0b);
                c.Get(1); c.Byte(0xad); c.Byte(0x3f); c.U(memory); c.Byte(0xad);
                c.I64(16); c.Byte(0x86); c.Byte(0x56); c.Byte(0x04); c.Byte(0x40);
                Trap(c, 7); c.Byte(0x0b);
                c.Get(1); c.Byte(0x24); c.U(memory);
            } else { c.Byte(0x23); c.U(memory); }
        });
        Save(fn, std::move(c));
        return fn;
    }

    uint32_t Access(uint8_t opcode) {
        if (auto it = accesses.find(opcode); it != accesses.end()) return it->second;
        uint8_t type;
        switch (opcode) {
            case 0x28: case 0x2c: case 0x2d: case 0x2e: case 0x2f:
            case 0x36: case 0x3a: case 0x3b: type = WasmModule::I32; break;
            case 0x29: case 0x30: case 0x31: case 0x32: case 0x33: case 0x34: case 0x35:
            case 0x37: case 0x3c: case 0x3d: case 0x3e: type = WasmModule::I64; break;
            case 0x2a: case 0x38: type = WasmModule::F32; break;
            case 0x2b: case 0x39: type = WasmModule::F64; break;
            default: throw CompileError {"wasm: unsupported scalar memory opcode"};
        }
        auto write = opcode >= 0x36;
        vector<uint8_t> params {WasmModule::I64}, results;
        if (write) params.push_back(type); else results.push_back(type);
        auto fn = module.AddFn(cat("goose.memory_op.", (int)opcode), params, results);
        accesses[opcode] = fn;
        WasmBytes c;
        Dispatch(c, 0, write ? 0x40 : type,
                 [&] { c.Get(0); c.I64(32); c.Byte(0x88); c.Byte(0xa7); }, [&](uint32_t memory) {
            c.Get(0); c.Byte(0xa7);
            if (write) c.Get(1);
            c.Mem(opcode, memory);
        });
        Save(fn, std::move(c));
        return fn;
    }
};

}  // namespace goose
