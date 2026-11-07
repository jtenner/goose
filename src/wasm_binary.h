// Goose compiler: direct WebAssembly binary encoding. No text assembler or C IR.
#pragma once

namespace goose {

struct WasmBytes {
    string bytes;
    void Byte(uint8_t b) { bytes += (char)b; }
    void U(uint64_t v) {
        if (v > UINT32_MAX) throw CompileError {"wasm: unsigned module field exceeds u32"};
        do {
            auto b = (uint8_t)(v & 127);
            v >>= 7;
            Byte(b | (v ? 128 : 0));
        } while (v);
    }
    void S(int64_t v) {
        bool more;
        do {
            auto b = (uint8_t)(v & 127);
            v >>= 7;
            more = !((v == 0 && !(b & 64)) || (v == -1 && (b & 64)));
            Byte(b | (more ? 128 : 0));
        } while (more);
    }
    void Name(string_view s) { U(s.size()); bytes.append(s); }
    void Append(const WasmBytes &b) { bytes += b.bytes; }
    void Section(uint8_t id, const WasmBytes &b) { Byte(id); U(b.bytes.size()); Append(b); }
    void I32(int32_t v) { Byte(0x41); S(v); }
    void I64(int64_t v) { Byte(0x42); S(v); }
    void F32(float v) {
        Byte(0x43);
        auto bits = bit_cast<uint32_t>(v);
        for (int i = 0; i < 4; i++) Byte((uint8_t)(bits >> (8 * i)));
    }
    void F64(double v) {
        Byte(0x44);
        auto bits = bit_cast<uint64_t>(v);
        for (int i = 0; i < 8; i++) Byte((uint8_t)(bits >> (8 * i)));
    }
    void Get(uint32_t v) { Byte(0x20); U(v); }
    void Set(uint32_t v) { Byte(0x21); U(v); }
    void Tee(uint32_t v) { Byte(0x22); U(v); }
    void Call(uint32_t f) { Byte(0x10); U(f); }
    void Copy(uint32_t destination, uint32_t source) { Byte(0xfc); U(10); U(destination); U(source); }
    // All packed accesses use an alignment hint of one byte. A nonzero memory
    // index is explicit in the multi-memory memarg, before its offset.
    void Mem(uint8_t op, uint32_t memory = 0, uint32_t offset = 0) {
        Byte(op); U(memory ? 64 : 0);
        if (memory) U(memory);
        U(offset);
    }
};

struct WasmModule {
    enum : uint8_t { I32 = 0x7f, I64 = 0x7e, F32 = 0x7d, F64 = 0x7c };
    struct Signature {
        vector<uint8_t> params, results;
        bool operator==(const Signature &) const = default;
    };
    struct Import { string module, name; uint32_t type; };
    struct Function { uint32_t type; vector<uint8_t> locals; WasmBytes code; string name; };
    struct Export { string name; uint8_t kind; uint32_t index; };
    vector<Signature> types;
    vector<Import> imports;
    vector<Function> functions;
    vector<Export> exports;
    // Static and global bytes share an immutable-address prefix. Activation
    // storage starts after it; address zero never denotes a live object.
    string data = string(8, '\0');
    uint32_t memories = 1;
    uint32_t Type(vector<uint8_t> params, vector<uint8_t> results) {
        Signature sig {std::move(params), std::move(results)};
        auto it = find(types.begin(), types.end(), sig);
        if (it != types.end()) return (uint32_t)(it - types.begin());
        types.push_back(std::move(sig));
        return (uint32_t)types.size() - 1;
    }
    uint32_t ImportFn(string name, vector<uint8_t> params, vector<uint8_t> results) {
        auto t = Type(std::move(params), std::move(results));
        imports.push_back({"goose", std::move(name), t});
        return (uint32_t)imports.size() - 1;
    }
    uint32_t AddFn(string name, vector<uint8_t> params, vector<uint8_t> results) {
        auto t = Type(std::move(params), std::move(results));
        functions.push_back({t, {}, {}, std::move(name)});
        return (uint32_t)(imports.size() + functions.size() - 1);
    }
    uint32_t Data(string_view bytes) {
        auto end = fragments.empty() ? data.size() : dataend;
        if (bytes.size() > UINT32_MAX || end > UINT32_MAX - bytes.size())
            throw CompileError {"wasm: static data exceeds memory32"};
        auto offset = (uint32_t)end;
        if (fragments.empty()) data.append(bytes);
        else {
            auto &last = fragments.back();
            if (last.first + last.second.size() == offset) last.second.append(bytes);
            else fragments.emplace_back(offset, string(bytes));
            dataend += (uint32_t)bytes.size();
        }
        return offset;
    }
    // Guest memory starts zeroed. Reserve large inline globals without
    // allocating or serializing their unused capacity in the compiler.
    vector<pair<uint32_t, string>> fragments;
    uint32_t dataend = 0;
    uint32_t ZeroData(uint32_t bytes) {
        auto end = fragments.empty() ? data.size() : dataend;
        if (end > UINT32_MAX - bytes) throw CompileError {"wasm: static data exceeds memory32"};
        if (fragments.empty()) fragments.emplace_back(0, std::move(data));
        dataend = (uint32_t)end + bytes;
        return (uint32_t)end;
    }
    string Finish() {
        auto end = fragments.empty() ? data.size() : dataend;
        if (end > UINT32_MAX - 15)
            throw CompileError {"wasm: static data exceeds memory32"};
        auto top = ((uint32_t)end + 15) & ~15u;
        WasmBytes out;
        out.bytes = string("\0asm\x01\0\0\0", 8);
        WasmBytes t;
        t.U(types.size());
        for (auto &sig : types) {
            t.Byte(0x60); t.U(sig.params.size());
            for (auto p : sig.params) t.Byte(p);
            t.U(sig.results.size());
            for (auto r : sig.results) t.Byte(r);
        }
        out.Section(1, t);
        if (!imports.empty()) {
            WasmBytes im; im.U(imports.size());
            for (auto &i : imports) {
                im.Name(i.module); im.Name(i.name); im.Byte(0); im.U(i.type);
            }
            out.Section(2, im);
        }
        WasmBytes fs; fs.U(functions.size());
        for (auto &f : functions) fs.U(f.type);
        out.Section(3, fs);
        WasmBytes ms; ms.U(memories);
        for (uint32_t i = 0; i < memories; i++) {
            ms.Byte(1); ms.U(i ? 1 : ((uint64_t)top + 65535) / 65536); ms.U(65536);
        }
        out.Section(5, ms);
        // One mutable top per physical memory. Memory 0 starts after static
        // data; data memories reserve offset zero and otherwise start empty.
        WasmBytes gs; gs.U(memories);
        for (uint32_t i = 0; i < memories; i++) {
            gs.Byte(I32); gs.Byte(1); gs.I32(i ? 1 : (int32_t)top); gs.Byte(0x0b);
        }
        out.Section(6, gs);
        WasmBytes es; es.U(exports.size());
        for (auto &e : exports) { es.Name(e.name); es.Byte(e.kind); es.U(e.index); }
        out.Section(7, es);
        WasmBytes cs; cs.U(functions.size());
        for (auto &f : functions) {
            WasmBytes body;
            // Group adjacent locals of the same type, keeping their indices.
            size_t groups = 0;
            for (size_t i = 0; i < f.locals.size(); i++)
                if (!i || f.locals[i] != f.locals[i - 1]) groups++;
            body.U(groups);
            for (size_t i = 0; i < f.locals.size();) {
                size_t end = i + 1;
                while (end < f.locals.size() && f.locals[end] == f.locals[i]) end++;
                body.U(end - i); body.Byte(f.locals[i]); i = end;
            }
            body.Append(f.code); body.Byte(0x0b);
            cs.U(body.bytes.size()); cs.Append(body);
        }
        out.Section(10, cs);
        WasmBytes ds; ds.U(fragments.empty() ? 1 : fragments.size());
        auto segment = [&](uint32_t offset, const string &bytes) {
            ds.U(0); ds.I32((int32_t)offset); ds.Byte(0x0b); ds.Name(bytes);
        };
        if (fragments.empty()) segment(0, data);
        else for (auto &[offset, bytes] : fragments) segment(offset, bytes);
        out.Section(11, ds);
        WasmBytes names, fnnames;
        fnnames.U(functions.size());
        for (size_t i = 0; i < functions.size(); i++) {
            fnnames.U(imports.size() + i); fnnames.Name(functions[i].name);
        }
        names.Name("name"); names.Byte(1); names.U(fnnames.bytes.size()); names.Append(fnnames);
        out.Section(0, names);
        return out.bytes;
    }
};

}  // namespace goose
