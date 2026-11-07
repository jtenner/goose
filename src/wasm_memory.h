// Memory32 data-stack helpers. Each logical stack has a distinct physical
// memory and top. Packed addresses use high u32 memory / low u32 offset.
#pragma once

namespace goose {

struct WasmMemoryRuntime {
    WasmModule &module;
    uint32_t failure;
    unordered_map<uint32_t, uint32_t> reserves;
    unordered_map<uint64_t, uint32_t> accesses;
    uint32_t dynamicreserve = UINT32_MAX, gettop = UINT32_MAX, settop = UINT32_MAX;
    uint32_t copyfromframe = UINT32_MAX;
    uint32_t copy = UINT32_MAX;
    uint32_t readprefix = UINT32_MAX;

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

    uint32_t Access(uint8_t opcode, uint32_t offset = 0) {
        auto key = ((uint64_t)offset << 8) | opcode;
        if (auto it = accesses.find(key); it != accesses.end()) return it->second;
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
        auto name = cat("goose.memory_op.", (int)opcode);
        if (offset) name += cat(".offset.", offset);
        auto fn = module.AddFn(name, params, results);
        accesses[key] = fn;
        WasmBytes c;
        Dispatch(c, 0, write ? 0x40 : type,
                 [&] { c.Get(0); c.I64(32); c.Byte(0x88); c.Byte(0xa7); }, [&](uint32_t memory) {
            c.Get(0); c.Byte(0xa7);
            if (write) c.Get(1);
            c.Mem(opcode, memory, offset);
        });
        Save(fn, std::move(c));
        return fn;
    }

    uint32_t CopyFromFrame() {
        if (copyfromframe != UINT32_MAX) return copyfromframe;
        copyfromframe = module.AddFn("goose.copy_from_frame",
                                    {WasmModule::I64, WasmModule::I32, WasmModule::I32}, {});
        WasmBytes c;
        Dispatch(c, 0, 0x40,
                 [&] { c.Get(0); c.I64(32); c.Byte(0x88); c.Byte(0xa7); },
                 [&](uint32_t memory) {
            c.Get(0); c.Byte(0xa7); c.Get(1); c.Get(2);
            c.Copy(memory, 0);
        });
        Save(copyfromframe, std::move(c));
        return copyfromframe;
    }

    uint32_t ReadPrefix() {
        if (readprefix != UINT32_MAX) return readprefix;
        readprefix = module.AddFn("goose.read_array_prefix", {WasmModule::I64},
                                  {WasmModule::I64, WasmModule::I32});
        WasmBytes c;
        // Locals: decoded count, bytes consumed, current byte, byte offset.
        // Dispatch once, then all decoder loads use the selected memory.
        Dispatch(c, 0, 0x40,
                 [&] { c.Get(0); c.I64(32); c.Byte(0x88); c.Byte(0xa7); },
                 [&](uint32_t memory) {
            c.Get(0); c.Byte(0xa7); c.Mem(0x31, memory); c.Tee(3);
            c.I64(128); c.Byte(0x54); c.Byte(0x04); c.Byte(0x40);
            // The common one-byte prefix needs no decode loop.
            c.Get(3); c.Set(1); c.I32(1); c.Set(2);
            c.Byte(0x05);
            c.Get(3); c.I64(127); c.Byte(0x83); c.Set(1);
            c.I32(1); c.Set(2);
            c.Byte(0x02); c.Byte(0x40); c.Byte(0x03); c.Byte(0x40);
            c.Get(0); c.I64(UINT32_MAX); c.Byte(0x83);
            c.Get(2); c.Byte(0xad); c.Byte(0x7c); c.Tee(4);
            c.I64(UINT32_MAX); c.Byte(0x56); c.Byte(0x04); c.Byte(0x40);
            Trap(c, 11); c.Byte(0x0b);
            c.Get(4); c.Byte(0xa7); c.Mem(0x31, memory); c.Set(3);
            // At most ten bytes, no payload above bit 63, shortest encoding.
            c.Get(2); c.I32(9); c.Byte(0x46);
            c.Get(3); c.I64(1); c.Byte(0x56); c.Byte(0x71);
            c.Get(3); c.Byte(0x50); c.Byte(0x72);
            c.Byte(0x04); c.Byte(0x40); Trap(c, 13); c.Byte(0x0b);
            c.Get(1); c.Get(3); c.I64(127); c.Byte(0x83);
            c.Get(2); c.I32(7); c.Byte(0x6c); c.Byte(0xad); c.Byte(0x86);
            c.Byte(0x84); c.Set(1);
            c.Get(2); c.I32(1); c.Byte(0x6a); c.Set(2);
            c.Get(3); c.I64(128); c.Byte(0x83); c.Byte(0x50);
            c.Byte(0x0d); c.U(1); c.Byte(0x0c); c.U(0);
            c.Byte(0x0b); c.Byte(0x0b); c.Byte(0x0b);
        });
        c.Get(1); c.Get(2);
        Save(readprefix, std::move(c), {WasmModule::I64, WasmModule::I32,
                                       WasmModule::I64, WasmModule::I64});
        return readprefix;
    }

    uint32_t Copy() {
        if (copy != UINT32_MAX) return copy;
        copy = module.AddFn("goose.copy_memory", {WasmModule::I64, WasmModule::I64, WasmModule::I32}, {});
        WasmBytes c;
        // A single shared fallback covers pairs of dynamic identities. Both
        // indices are concrete at each memory.copy. The backend's fixed
        // memory limit bounds this helper; callers with known indices emit
        // one instruction and do not use this table.
        Dispatch(c, 0, 0x40,
                 [&] { c.Get(0); c.I64(32); c.Byte(0x88); c.Byte(0xa7); },
                 [&](uint32_t destination) {
            Dispatch(c, 0, 0x40,
                     [&] { c.Get(1); c.I64(32); c.Byte(0x88); c.Byte(0xa7); },
                     [&](uint32_t source) {
                c.Get(0); c.Byte(0xa7); c.Get(1); c.Byte(0xa7); c.Get(2);
                c.Copy(destination, source);
            });
        });
        Save(copy, std::move(c));
        return copy;
    }
};

}  // namespace goose
