// Goose compiler: native scalar WebAssembly lowering. Reads the checked AST;
// it never calls CodeGen or emits C. Compound layouts await shared storage IR.
#pragma once

namespace goose {

struct WasmCodeGen : ValueLayout {
    Ast &ast;
    WasmModule module;
    WasmValueSupport support;
    WasmStoragePlan storage;
    optional<WasmMemoryRuntime> memories;
    WasmBytes code;
    FnSpec *current = nullptr;
    uint32_t fn = 0;
    uint32_t framebase = 0, framesize = 0;
    uint32_t reservefn, initfn, startfn;
    uint32_t beginprint, printint, printfloat, printbool, printbytes, endprint;
    uint32_t snapshotbytes = UINT32_MAX, printsnapshot = UINT32_MAX, dropsnapshot = UINT32_MAX;
    uint32_t nextprint = 0;
    uint32_t failfn, exitfn, fmodfn, f2islowfn;
    uint32_t f2ifn = UINT32_MAX;
    uint32_t fixedoffsetscratch = UINT32_MAX;
    array<uint32_t, 4> fixedfillitems;
    uint32_t fixedfillposition = UINT32_MAX, fixedfillbase = UINT32_MAX;
    uint32_t arraystorevalue = UINT32_MAX;
    struct Slot { TypeExpr *type; uint32_t local = 0, offset = 0; bool memory = false, global = false; };
    struct FixedPlace {
        TypeExpr *type;
        uint32_t address, offset = 0;
        int memory = 0;
        bool packed = false, bounded = false;
    };
    static constexpr uint32_t NoLocal = UINT32_MAX;
    struct FixedMathOperand {
        FixedPlace place;
        uint32_t value = NoLocal; // A captured broadcast scalar, otherwise a stored aggregate.
    };
    enum class ArrayImage { Inline, PrefixedData, GrowableHeader };
    enum class ArrayOrigin { PlannedOwner, ParentPlace, ReferenceABI, FreshDataElement };
    struct ArrayLayoutFacts {
        TypeExpr *type, *element;
        ArrayImage image;
        uint32_t stride;
        int64_t capacity;
        ArrayPrefixLayout prefix;
        bool varint;
    };
    struct ArrayPlace {
        FixedPlace image;
        ArrayLayoutFacts layout;
        int elementMemory;
        VarDef *owner = nullptr;
        ArrayOrigin origin = ArrayOrigin::ReferenceABI;
        const Slot *ownerSlot = nullptr; // Retain direct frame-owner address emission without a new local.
    };
    struct ArrayView {
        ArrayPlace place;
        uint32_t length = NoLocal, prefixBytes = NoLocal;
    };
    // The selected packed i64 address remains on the operand stack.
    struct ElementPlace { TypeExpr *type; int memory; bool bounded = true; };
    enum class FreshFixedOrigin { PlannedFrame, ReservedDataElement, ReservedFrameTemporary, IncomingResult };
    struct FixedTemporaryOwner {
        TypeExpr *type;
        Node *expression;
        uint32_t baseLocal, image, bytes;
        size_t scope;
    };
    struct FreshFixedDestination {
        FixedPlace place;
        VarDef *root;
        uint32_t rootOffset = 0, image = 0;
        FreshFixedOrigin origin = FreshFixedOrigin::PlannedFrame;
        Node *initialization = nullptr;
        uint32_t ownerBytes = 0;
        const FixedTemporaryOwner *temporary = nullptr;
    };
    struct FreshDataArrayDestination {
        ArrayPlace image;
        VarDef *root;
        VarDecl *initialization;
        uint32_t logicalStack, identityLocal, baseLocal, bytesLocal, countLocal;
        uint32_t prefixBytes, stride;
        uint32_t literalCount = NoLocal, ownerBytes = 0;
    };
    struct FixedFields {
        const vector<Field> &fields;
        const vector<TypeExpr *> &types;
        const Layout &layout;
    };
    struct PushScratch { uint32_t item, length, old, address, base, offset; };
    array<optional<PushScratch>, 4> fixedpushscratch;
    unordered_map<VarDef *, Slot> globals, slots;
    unordered_map<FnSpec *, uint32_t> functions;
    set<VarDef *> addressed;
    struct CleanupAction {
        Defer *deferred = nullptr;
        uint32_t memory = 0, top = 0; // Snapshot actions use memory as a compiler print id.
        bool dynamic = false;
        uint32_t snapshot = UINT32_MAX;
    };
    vector<vector<CleanupAction>> scopes;
    struct Target {
        enum Kind { Function, Inline, Loop, Early } kind;
        SFunction *sf = nullptr;
        size_t scope = 0;
        int label = 0, cont = -1;
        int result = -1;
        TypeExpr *type = nullptr;
        const FreshFixedDestination *destination = nullptr;
    };
    vector<Target> targets;
    vector<int> labels;
    int nextlabel = 0;

    explicit WasmCodeGen(Ast &a) : ast(a), support(*this), storage(a, *this) {}
    static bool Aggregate(TypeExpr *t) {
        return t && (t->kind == TY_ARRAY || t->kind == TY_STRUCT || t->kind == TY_ENUM ||
                     t->kind == TY_VARIANT || t->kind == TY_SLICE);
    }
    static bool Nominal(TypeExpr *t) { return WasmValueSupport::Nominal(t); }
    uint32_t RequireFixed(TypeExpr *t, Line line) {
        if (auto reason = support.Check(t)) Fail(line, reason);
        uint64_t bytes;
        if (!TryFixedSize(t, UINT32_MAX, bytes, support.sizes))
            Fail(line, "fixed aggregate layout exceeds memory32");
        return (uint32_t)bytes;
    }
    bool FixedParameter(TypeExpr *t) { return storage.FixedParameter(t); }
    bool FixedResult(TypeExpr *t) { return FixedParameter(t); }
    void RequireCallValue(TypeExpr *t, bool result, Line line) {
        if (FixedParameter(t)) {
            RequireFixed(t, line);
            return;
        }
        if (t->kind == TY_ARRAY)
            Fail(line, result ? "array results need the pending destination lowering"
                              : "by-value arrays need the pending destination lowering");
        if (Aggregate(t)) Fail(line, "by-value aggregates need the pending destination lowering");
    }
    bool FatPointers() const { return storage.dataaddresses; }
    bool HeaderRef(TypeExpr *t) {
        return t->kind == TY_REF && t->ref->sub->kind == TY_ARRAY && IsResz(t->ref->sub);
    }
    uint8_t ReferenceABI(TypeExpr *t) {
        assert(t->kind == TY_REF);
        return FatPointers() && !HeaderRef(t) ? WasmModule::I64 : WasmModule::I32;
    }
    bool VariableArray(TypeExpr *t) { return t->kind == TY_ARRAY && t->arr->akind == A_VAR; }
    bool RuntimeLimited(TypeExpr *t) {
        return t->kind == TY_ARRAY && t->arr->akind == A_LIMITED && ArrSize(t->arr) < 0;
    }
    bool DataArray(TypeExpr *t) { return VariableArray(t) || RuntimeLimited(t); }
    bool VarintPrefix(TypeExpr *t) { return VariableArray(t) && LenStore(t->arr) == IS_VARINT; }
    uint32_t DataPrefix(TypeExpr *t) {
        auto prefix = ArrayPrefix(t->arr).elements;
        assert(prefix >= 0);
        return (uint32_t)prefix;
    }
    uint32_t DataPrefix(TypeExpr *t, uint64_t count) {
        if (!VarintPrefix(t)) return DataPrefix(t);
        uint32_t bytes = 1;
        while (count >= 128) { count >>= 7; bytes++; }
        return bytes;
    }
    bool InlineArray(TypeExpr *t) {
        return t->kind == TY_ARRAY && (t->arr->akind == A_FIXED ||
               (t->arr->akind == A_LIMITED && ArrSize(t->arr) >= 0));
    }
    TypeExpr *ByteArray(TypeExpr *t) {
        while (t && t->kind == TY_REF) t = t->ref->sub;
        return t && t->kind == TY_ARRAY && t->arr->sub->kind == TY_INT &&
               t->arr->sub->intstorage == IS_U8 ? t : nullptr;
    }
    bool NeedsBase(FnSpec *sp) { return storage.counts.need[sp] && storage.Base(sp) < 0; }
    void StackIndex(uint32_t offset) {
        auto base = storage.Base(current);
        if (base >= 0) code.I32(base + (int32_t)offset);
        else { code.Get((uint32_t)current->params.size()); code.I32(offset); code.Byte(0x6a); }
    }
    [[noreturn]] void Fail(Line l, const string &message) {
        Diagnostic d;
        d.where = LocOf(l);
        d.message = cat("wasm target: ", message);
        d.text = RenderDiagnostic(d, l.fileidx >= 0 && l.fileidx < (int)ast.sources.size()
                                      ? ast.sources[l.fileidx].first : string(), {});
        throw CompileError {d.text, {d}};
    }
    static bool Void(TypeExpr *t) { return !t || t->kind == TY_VOID; }
    uint8_t Type(TypeExpr *t) {
        if (!t) Fail({}, "missing checked type");
        switch (t->kind) {
            case TY_BOOL: return WasmModule::I32;
            case TY_INT:
                if (t->intstorage == IS_VARINT) Fail(t->line, "varint storage is not implemented");
                if (t->ix) Fail(t->line, "index and bound types are not implemented");
                return WasmModule::I64;
            case TY_FLT: return t->fltstorage == FS_F32 ? WasmModule::F32 : WasmModule::F64;
            case TY_REF:
                if (t->ref->lenstorage >= 0) Fail(t->line, "relative references are not implemented");
                if (Nominal(t->ref->sub)) RequireFixed(t->ref->sub, t->line);
                else Type(t->ref->sub);
                // A resizable header is in Memory 0. Ordinary pointees may
                // also lie in any assigned data memory.
                return ReferenceABI(t);
            case TY_ARRAY: {
                if (!IsResz(t) && !InlineArray(t) && !DataArray(t))
                    Fail(t->line, "this array layout needs the pending compound lowering");
                auto element = t->arr->sub;
                if (Nominal(element) && (InlineArray(t) || support.DataNominalArray(t))) {
                    if (InlineArray(t)) RequireFixed(t, t->line);
                    else {
                        if (auto reason = support.Check(t)) Fail(t->line, reason);
                        RequireFixed(element, t->line);
                    }
                    return BorrowedArrayAddressType(t);
                }
                if (!support.ScalarElement(element))
                    Fail(t->line, "compound array elements need the pending layout lowering");
                Type(element);
                if (InlineArray(t)) {
                    auto prefix = t->arr->akind == A_LIMITED ? IntSize(LenStore(t->arr)) : 0;
                    if ((uint64_t)ArrSize(t->arr) > (UINT32_MAX - prefix) / FixedSize(element))
                        Fail(t->line, "array layout exceeds memory32");
                }
                return BorrowedArrayAddressType(t);
            }
            default: Fail(t->line, "this value layout is not implemented (scalar backend)");
        }
    }
    uint32_t Size(TypeExpr *t) {
        if (Nominal(t)) return RequireFixed(t, t->line);
        Type(t);
        if (DataArray(t)) Fail(t->line, "variable array size needs the pending destination lowering");
        auto size = IsResz(t) ? 16 : FixedSize(t);
        if (size < 0 || size > UINT32_MAX) Fail(t->line, "value exceeds memory32");
        return (uint32_t)size;
    }
    uint32_t Local(uint8_t t) {
        auto &f = module.functions[fn - module.imports.size()];
        auto n = (uint32_t)(module.types[f.type].params.size() + f.locals.size());
        f.locals.push_back(t);
        return n;
    }
    uint32_t Temp(TypeExpr *t) { return Local(Type(t)); }
    int Open(uint8_t op = 0x02, uint8_t type = 0x40) {
        code.Byte(op); code.Byte(type);
        auto label = nextlabel++;
        labels.push_back(label);
        return label;
    }
    void Close() { assert(!labels.empty()); code.Byte(0x0b); labels.pop_back(); }
    void Branch(int label, bool conditional = false) {
        auto it = find(labels.rbegin(), labels.rend(), label);
        assert(it != labels.rend());
        code.Byte(conditional ? 0x0d : 0x0c); code.U(it - labels.rbegin());
    }
    void Trap(int error, Line l) {
        auto file = l.fileidx >= 0 && l.fileidx < (int)ast.sources.size()
                      ? ast.sources[l.fileidx].first : string();
        auto offset = module.Data(file);
        code.I32(error); code.I32((int32_t)offset); code.I32((int32_t)file.size());
        code.I32(l.line); code.Call(failfn); code.Byte(0x00);
    }
    void CheckNull(Line l, uint8_t type = 0) {
        if (!type) type = FatPointers() ? WasmModule::I64 : WasmModule::I32;
        auto p = Local(type);
        code.Tee(p); code.Byte(type == WasmModule::I64 ? 0x50 : 0x45);
        Open(0x04); Trap(4, l); Close(); code.Get(p);
    }
    void Normalize(TypeExpr *t) {
        if (t->kind != TY_INT) return;
        auto bits = IntBits(t->intstorage);
        if (bits == 64) return;
        if (IsUnsigned(t->intstorage)) {
            code.I64((int64_t)((1ull << bits) - 1)); code.Byte(0x83);
        } else code.Byte(bits == 8 ? 0xc2 : bits == 16 ? 0xc3 : 0xc4);
    }
    void Convert(TypeExpr *from, TypeExpr *to) {
        if (Nominal(from) || Nominal(to))
            Fail(to ? to->line : from->line, "aggregate values need the pending destination lowering");
        if (!to || from == to) return;
        // A bare null has the checker's optional-void placeholder. It has no
        // pointee layout to lower; only its zero address needs conversion.
        if (from->kind == TY_REF && from->ref->sub->kind == TY_VOID && to->kind == TY_REF) {
            auto source = FatPointers() ? WasmModule::I64 : WasmModule::I32;
            auto target = Type(to);
            if (source != target) code.Byte(target == WasmModule::I32 ? 0xa7 : 0xad);
            return;
        }
        while (from->kind == TY_REF && to->kind != TY_REF) {
            CheckNull(from->line, Type(from)); from = from->ref->sub; Load(from);
        }
        auto f = Type(from), t = Type(to);
        if (from->kind == TY_INT && to->kind == TY_FLT) {
            code.Byte(t == WasmModule::F32 ? (IsUnsigned(from->intstorage) ? 0xb5 : 0xb4)
                                          : (IsUnsigned(from->intstorage) ? 0xba : 0xb9));
        } else if (from->kind == TY_FLT && to->kind == TY_INT) {
            if (f == WasmModule::F32) code.Byte(0xbb);
            if (f2ifn == UINT32_MAX)
                f2ifn = module.AddFn("goose.float_to_int", {WasmModule::F64}, {WasmModule::I64});
            code.Call(f2ifn);
        } else if (f != t && from->kind == TY_FLT && to->kind == TY_FLT) {
            code.Byte(t == WasmModule::F32 ? 0xb6 : 0xbb);
        } else if (f != t) Fail(to->line, "unsupported scalar conversion");
        Normalize(to);
    }
    uint8_t LoadOpcode(TypeExpr *t) {
        switch (t->kind) {
            case TY_BOOL: return 0x2d;
            case TY_INT: {
                auto bits = IntBits(t->intstorage);
                auto uns = IsUnsigned(t->intstorage);
                return bits == 64 ? 0x29 : bits == 32 ? (uns ? 0x35 : 0x34)
                                  : bits == 16 ? (uns ? 0x33 : 0x32) : (uns ? 0x31 : 0x30);
            }
            case TY_FLT: return t->fltstorage == FS_F32 ? 0x2a : 0x2b;
            case TY_REF: return 0x29;
            default: Fail(t->line, "this load layout is not implemented");
        }
    }
    void LoadFixed(TypeExpr *t, uint32_t memory = 0, uint32_t offset = 0) {
        code.Mem(LoadOpcode(t), memory, offset);
        if (t->kind == TY_REF && Type(t) == WasmModule::I32) code.Byte(0xa7);
    }
    void Load(TypeExpr *t) {
        if (t->kind == TY_ARRAY) return; // Its reference already denotes the header.
        if (!FatPointers()) { LoadFixed(t); return; }
        code.Call(memories->Access(LoadOpcode(t)));
        if (t->kind == TY_REF && Type(t) == WasmModule::I32) code.Byte(0xa7);
    }
    uint8_t StoreOpcode(TypeExpr *t) {
        switch (t->kind) {
            case TY_BOOL: return 0x3a;
            case TY_INT: {
                auto bits = IntBits(t->intstorage);
                return bits == 64 ? 0x37 : bits == 32 ? 0x3e : bits == 16 ? 0x3d : 0x3c;
            }
            case TY_FLT: return t->fltstorage == FS_F32 ? 0x38 : 0x39;
            case TY_REF: return 0x37;
            default: Fail(t->line, "this store layout is not implemented");
        }
    }
    void StoreFixed(TypeExpr *t, uint32_t memory = 0, uint32_t offset = 0) {
        if (HeaderRef(t)) {
            if (offset > UINT32_MAX - 8) Fail(t->line, "reference layout exceeds memory32");
            auto value = Local(WasmModule::I32), at = Local(WasmModule::I32);
            code.Set(value); code.Set(at);
            code.Get(at); code.Get(value); code.Byte(0xad); code.Mem(0x37, memory, offset);
            code.Get(at); code.Get(value); Open(0x04, WasmModule::I64);
            code.Get(value); code.Mem(0x29); code.I64(32); code.Byte(0x88);
            code.Byte(0x05); code.I64(0); Close(); code.Mem(0x37, memory, offset + 8);
            return;
        }
        if (t->kind == TY_REF && Type(t) == WasmModule::I32) code.Byte(0xad);
        code.Mem(StoreOpcode(t), memory, offset);
    }
    void Store(TypeExpr *t) {
        if (!FatPointers()) { StoreFixed(t); return; }
        if (HeaderRef(t)) Fail(t->line, "dynamic compound-reference stores are not implemented");
        if (t->kind == TY_REF && Type(t) == WasmModule::I32) code.Byte(0xad);
        code.Call(memories->Access(StoreOpcode(t)));
    }
    Slot &Find(VarDef *v) {
        auto g = globals.find(v);
        if (g != globals.end()) return g->second;
        auto it = slots.find(v);
        if (it == slots.end()) Fail(v->line, "out-of-line captured locals are not implemented");
        return it->second;
    }
    void Address(const Slot &s) {
        assert(s.memory);
        if (s.global) code.I32((int32_t)s.offset);
        else { code.Get(framebase); code.I32((int32_t)s.offset); code.Byte(0x6a); }
    }
    void Read(const Slot &s) {
        if (s.memory) {
            Address(s);
            if (DataArray(s.type)) code.Mem(0x29);
            else if (s.type->kind != TY_ARRAY) LoadFixed(s.type);
            else if (BorrowedArrayAddressType(s.type) == WasmModule::I64) code.Byte(0xad);
        }
        else code.Get(s.local);
    }
    void ReferenceAddress(const Slot &s) {
        if (DataArray(s.type)) Read(s);
        else {
            Address(s);
            if (s.type->kind == TY_ARRAY ? BorrowedArrayAddressType(s.type) == WasmModule::I64
                                        : FatPointers()) code.Byte(0xad);
        }
    }
    void Write(const Slot &s) {
        if (s.memory) {
            auto temp = Temp(s.type); code.Set(temp); Address(s); code.Get(temp);
            if (DataArray(s.type)) code.Mem(0x37);
            else StoreFixed(s.type);
        } else code.Set(s.local);
    }
    void Bind(VarDef *v, optional<uint32_t> param = {}) {
        if (v->isglobal || slots.count(v)) return;
        if (auto it = storage.fixedvalues.find(v); it != storage.fixedvalues.end()) {
            auto bytes = it->second.bytes;
            if (framesize > UINT32_MAX - bytes) Fail(v->line, "frame exceeds memory32");
            slots[v] = {v->type, 0, framesize, true, false};
            framesize += bytes;
            return;
        }
        auto t = Type(v->type);
        Slot s {v->type};
        if (!DataArray(v->type) && (addressed.count(v) || v->type->kind == TY_ARRAY)) {
            s.memory = true;
            s.offset = framesize;
            auto bytes = std::max(1u, Size(v->type));
            if (framesize > UINT32_MAX - bytes) Fail(v->line, "frame exceeds memory32");
            framesize += bytes;
        } else s.local = param ? *param : Local(t);
        slots[v] = s;
    }
    void Scan(Node *n) {
        if (!n || Is<FnDecl>(n)) return;
        if (auto u = Is<Unary>(n); u && u->op == T_BITAND) {
            if (auto id = Is<Ident>(u->child); id && id->vdef)
                addressed.insert(id->vdef);
        }
        if (auto a = Is<goose::Assign>(n); a && a->op == T_DOTASSIGN)
            if (auto id = Is<Ident>(a->rhs); id && id->vdef && id->vdef->type->kind != TY_REF)
                addressed.insert(id->vdef);
        RunChildren(n, [&](Node *ch) { Scan(ch); });
    }
    void BindTree(Node *n) {
        if (!n || Is<FnDecl>(n)) return;
        if (auto v = Is<VarDecl>(n)) for (auto d : v->defs) Bind(d);
        if (auto f = Is<ForLoop>(n)) {
            if (Nominal(f->vdef->type)) {
                auto plan = storage.fixedvalues.find(f->vdef);
                if (plan == storage.fixedvalues.end() ||
                    plan->second.origin != WasmStoragePlan::FixedOrigin::IterationCopy ||
                    plan->second.initialization != f || plan->second.argument || !plan->second.initialized)
                    Fail(f->line, "by-value aggregate iteration needs its planned copy owner");
            }
            Bind(f->vdef); if (f->idxdef) Bind(f->idxdef);
        }
        if (auto match = Is<MatchExpr>(n))
            for (auto &arm : match->arms) if (arm.binder) Bind(arm.binder);
        if (auto c = Is<Call>(n); c && c->fvbody) {
            for (auto v : c->fvparams) { RequireCallValue(v->type, false, c->line); Bind(v); }
            for (auto t : c->rettypes) RequireCallValue(t, true, c->line);
        }
        RunChildren(n, [&](Node *ch) { BindTree(ch); });
    }
    void Cleanup(size_t bottom) {
        // Copy each list. Emitting a deferred body opens scopes of its own.
        for (size_t i = scopes.size(); i > bottom; i--) {
            auto list = scopes[i - 1];
            for (auto it = list.rbegin(); it != list.rend(); ++it) {
                if (it->snapshot != UINT32_MAX) { code.Get(it->snapshot); code.Call(dropsnapshot); }
                else if (it->deferred) BlockValue(it->deferred->body, false);
                else if (it->dynamic) {
                    code.Get(it->memory); code.Get(it->top); code.Call(memories->Top(true));
                } else { code.Get(it->top); code.Byte(0x24); code.U(it->memory); }
            }
        }
    }
    void BlockValue(Block *b, bool value, TypeExpr *wanted = nullptr) {
        scopes.emplace_back();
        for (auto n : b->stmts) Statement(n);
        int result = -1;
        if (b->tail) {
            if (value && !Void(b->tail->exprtype)) {
                Gen(b->tail);
                auto type = wanted ? wanted : b->tail->exprtype;
                Convert(b->tail->exprtype, type); result = (int)Temp(type); code.Set(result);
            } else Statement(b->tail);
        }
        Cleanup(scopes.size() - 1);
        scopes.pop_back();
        if (result >= 0) code.Get(result);
    }
    TypeExpr *Operand(TypeExpr *t) { return t->kind == TY_REF ? t->ref->sub : t; }
    void Arithmetic(TType op, TypeExpr *t, Line line) {
        if (t->kind == TY_FLT) {
            auto f32 = t->fltstorage == FS_F32;
            if (op == T_MOD) {
                auto r = Temp(t); code.Set(r);
                if (f32) code.Byte(0xbb);
                code.Get(r); if (f32) code.Byte(0xbb);
                code.Call(fmodfn); if (f32) code.Byte(0xb6);
                return;
            }
            auto base = f32 ? 0x92 : 0xa0;
            code.Byte((uint8_t)(base + (op == T_PLUS ? 0 : op == T_MINUS ? 1 : op == T_MUL ? 2 : 3)));
            return;
        }
        if (t->kind != TY_INT) Fail(line, "arithmetic needs a scalar numeric type");
        auto uns = IsUnsigned(t->intstorage);
        if (op == T_DIV || op == T_MOD) {
            auto r = Temp(t), l = Temp(t); code.Set(r); code.Set(l);
            code.Get(r); code.Byte(0x50); Open(0x04); Trap(2, line); Close();
            if (op == T_MOD && !uns) {
                // rem_s traps only for zero. The min/-1 remainder is zero.
                code.Get(l); code.Get(r); code.Byte(0x81);
                auto rem = Temp(t); code.Tee(rem); code.I64(0); code.Byte(0x53);
                Open(0x04, WasmModule::I64);
                code.Get(rem); code.Get(r); code.I64(0); code.Byte(0x53);
                Open(0x04, WasmModule::I64);
                code.I64(0); code.Get(r); code.Byte(0x7d);
                code.Byte(0x05); code.Get(r); Close(); code.Byte(0x7c);
                code.Byte(0x05); code.Get(rem); Close();
            } else {
                if (!uns && IntBits(t->intstorage) == 64 && op == T_DIV) {
                    code.Get(l); code.I64(INT64_MIN); code.Byte(0x51);
                    code.Get(r); code.I64(-1); code.Byte(0x51); code.Byte(0x71);
                    Open(0x04); Trap(3, line); Close();
                }
                code.Get(l); code.Get(r); code.Byte(op == T_MOD ? 0x82 : uns ? 0x80 : 0x7f);
            }
        } else if (op == T_SHL || op == T_SHR) {
            code.I64(IntBits(t->intstorage) - 1); code.Byte(0x83);
            code.Byte(op == T_SHL ? 0x86 : uns ? 0x88 : 0x87);
        } else {
            switch (op) {
                case T_PLUS: code.Byte(0x7c); break;
                case T_MINUS: code.Byte(0x7d); break;
                case T_MUL: code.Byte(0x7e); break;
                case T_BITAND: code.Byte(0x83); break;
                case T_BITOR: code.Byte(0x84); break;
                case T_XOR: code.Byte(0x85); break;
                default: Fail(line, "unsupported scalar operator");
            }
        }
        Normalize(t);
    }
    void Truth(Node *n) {
        Gen(n);
        if (n->exprtype->kind == TY_REF) {
            code.Byte(ReferenceType(n) == WasmModule::I64 ? 0x50 : 0x45); code.Byte(0x45);
        }
    }
    void Condition(Node *n) {
        Gen(n);
        if (n->exprtype->kind == TY_REF && ReferenceType(n) == WasmModule::I64) {
            code.Byte(0x50); code.Byte(0x45);
        }
    }
    uint8_t ReferenceType(Node *n) {
        if (Is<NullLit>(n) && n->exprtype->kind == TY_REF && n->exprtype->ref->sub->kind == TY_VOID)
            return FatPointers() ? WasmModule::I64 : WasmModule::I32;
        if (auto actual = ActualType(n); actual && actual->kind == TY_REF) return Type(actual);
        return Type(n->exprtype);
    }
    void ReferenceValue(Node *n, uint8_t wanted = 0) {
        if (Is<NullLit>(n)) {
            if ((wanted ? wanted : ReferenceType(n)) == WasmModule::I64) code.I64(0); else code.I32(0);
            return;
        }
        // Narrowing can give an optional identifier its pointee's exprtype.
        // Identity and null tests still read the stored reference itself.
        if (auto id = Is<Ident>(n); id && id->vdef && id->vdef->type->kind == TY_REF) {
            Read(Find(id->vdef));
        } else if (auto actual = ActualType(n); actual && actual->kind == TY_REF &&
                   ReadFixedTemporary(n, actual)) {
            // Keep the temporary owner until its stored reference has been read.
        } else if (auto field = Is<Dot>(n); field && field->IsField() && ActualType(n)->kind == TY_REF) {
            ReadPlace(FieldPlace(field));
        } else if (auto index = Is<Index>(n); index && ActualType(n)->kind == TY_REF) {
            auto element = ElementAddress(index); LoadElement(element);
        } else if ((Is<Call>(n) || Is<InlineBlock>(n)) && ActualType(n)->kind == TY_REF) {
            Gen(n, ActualType(n));
        } else {
            if (!n->exprtype || n->exprtype->kind != TY_REF)
                Fail(n->line, "reference identity requires an address value");
            Gen(n);
        }
        if (wanted && ReferenceType(n) != wanted) {
            if (wanted != WasmModule::I64) Fail(n->line, "incompatible reference memory representation");
            code.Byte(0xad);
        }
    }
    void BinaryValue(Binary *n) {
        auto op = n->op;
        auto identity = op == T_DOTEQ || op == T_DOTNEQ;
        auto nulltest = (op == T_EQ || op == T_NEQ) && (Is<NullLit>(n->left) || Is<NullLit>(n->right));
        if (identity || nulltest) {
            auto pointer = FatPointers() ? WasmModule::I64 : WasmModule::I32;
            ReferenceValue(n->left, pointer); ReferenceValue(n->right, pointer);
            auto base = pointer == WasmModule::I64 ? 0x51 : 0x46;
            code.Byte(base + (op == T_NEQ || op == T_DOTNEQ));
            return;
        }
        if (n->op == T_ANDAND || n->op == T_OROR) {
            Condition(n->left); Open(0x04, WasmModule::I32);
            if (n->op == T_ANDAND) Truth(n->right); else code.I32(1);
            code.Byte(0x05);
            if (n->op == T_OROR) Truth(n->right); else code.I32(0);
            Close(); return;
        }
        auto t = Operand(n->left->exprtype);
        if (Nominal(t) && !(n->left->exprtype->kind == TY_REF &&
                                      n->left->exprtype->ref->optional))
            Fail(n->line, "aggregate value operators need the pending destination lowering");
        if ((t->kind == TY_ARRAY || t->kind == TY_SLICE) && !(n->left->exprtype->kind == TY_REF &&
                                    n->left->exprtype->ref->optional)) {
            if (op == T_EQ || op == T_NEQ) { ArrayEquality(n); return; }
            Fail(n->line, "array value operators need the pending compound lowering");
        }
        Gen(n->left); Gen(n->right);
        if (op == T_EQ || op == T_NEQ || op == T_DOTEQ || op == T_DOTNEQ ||
            op == T_LT || op == T_GT || op == T_LTEQ || op == T_GTEQ) {
            auto eq = op == T_EQ || op == T_DOTEQ;
            auto ne = op == T_NEQ || op == T_DOTNEQ;
            if (t->kind == TY_FLT) {
                auto base = t->fltstorage == FS_F32 ? 0x5b : 0x61;
                code.Byte((uint8_t)(base + (eq ? 0 : ne ? 1 : op == T_LT ? 2 : op == T_GT ? 3 : op == T_LTEQ ? 4 : 5)));
            } else {
                auto i32 = Type(n->left->exprtype) == WasmModule::I32;
                auto uns = t->kind == TY_INT && IsUnsigned(t->intstorage);
                auto base = i32 ? 0x46 : 0x51;
                code.Byte((uint8_t)(base + (eq ? 0 : ne ? 1 : op == T_LT ? (uns ? 3 : 2)
                                   : op == T_GT ? (uns ? 5 : 4) : op == T_LTEQ ? (uns ? 7 : 6) : (uns ? 9 : 8))));
            }
            return;
        }
        Arithmetic(op, t, n->line); Convert(t, n->exprtype);
    }
    void PrintScalar(uint32_t token, uint32_t value, TypeExpr *t) {
        code.Get(token); code.Get(value);
        if (t->kind == TY_INT) { code.I32(IsUnsigned(t->intstorage)); code.Call(printint); }
        else if (t->kind == TY_FLT) {
            if (t->fltstorage == FS_F32) code.Byte(0xbb);
            code.I32(t->fltstorage == FS_F32 ? 32 : 64); code.Call(printfloat);
        } else if (t->kind == TY_BOOL) code.Call(printbool);
        else Fail(t->line, "printing this value layout is not implemented");
    }
    uint32_t SnapshotByteArgument(Node *arg) {
        auto t = arg->exprtype;
        Gen(arg); auto value = Temp(t); code.Set(value);
        int null = -1;
        while (t->kind == TY_REF) {
            if (null < 0) { null = (int)Local(WasmModule::I32); code.I32(0); code.Set(null); }
            auto sub = t->ref->sub;
            auto loaded = Temp(sub);
            code.Get(null); code.Get(value); code.Byte(Type(t) == WasmModule::I64 ? 0x50 : 0x45);
            code.Byte(0x72); Open(0x04); code.I32(1); code.Set(null);
            code.Byte(0x05); code.Get(value); Load(sub); code.Set(loaded); Close();
            value = loaded; t = sub;
        }
        if (null >= 0) {
            code.Get(null); Open(0x04, WasmModule::I32);
            auto offset = module.Data("null");
            code.I32(0); code.I32((int32_t)offset); code.I32(4); code.Call(snapshotbytes);
            code.Byte(0x05);
        }
        auto place = RefineArrayOwner(CaptureArrayBorrow(t, value, BorrowedArrayAddressType(t),
                                                       ArrayOrigin::ReferenceABI, arg->line), arg);
        auto length = Local(WasmModule::I64), zero = Local(WasmModule::I64);
        auto prefix = place.layout.varint ? Local(WasmModule::I32) : NoLocal;
        auto view = CaptureArrayView(place, length, prefix);
        code.I64(0); code.Set(zero); ElementOffset(view, zero, arg->line);
        auto address = Local(WasmModule::I64); code.Set(address);
        code.Get(address); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
        code.Get(address); code.Byte(0xa7); code.Get(length); code.Byte(0xa7); code.Call(snapshotbytes);
        if (null >= 0) Close();
        auto snapshot = Local(WasmModule::I32); code.Set(snapshot);
        return snapshot;
    }
    void Print(Call *c) {
        if (!c->fmtspecs.empty()) Fail(c->line, "custom formatting is not implemented");
        // No type or literal denotes a captured byte snapshot in value.
        struct Piece { TypeExpr *type = nullptr; uint32_t value = 0; int null = -1; StrLit *literal = nullptr; };
        vector<Piece> pieces;
        if (nextprint == UINT32_MAX) Fail(c->line, "too many emitted print calls");
        auto printid = nextprint++;
        bool hassnapshots = false;
        // Snapshot scalar arguments before opening a host line. A return in
        // any argument must leave no host buffer behind. References are read
        // now too, before a later argument can mutate their pointees.
        for (auto arg : c->ValueArgNodes()) {
            if (auto literal = Is<StrLit>(arg)) { pieces.push_back({nullptr, 0, -1, literal}); continue; }
            if (ByteArray(arg->exprtype)) {
                auto snapshot = SnapshotByteArgument(arg);
                assert(!scopes.empty());
                scopes.back().push_back({nullptr, printid, 0, false, snapshot});
                hassnapshots = true;
                pieces.push_back({nullptr, snapshot, -1, nullptr});
                continue;
            }
            auto t = arg->exprtype;
            auto printed = t;
            while (printed->kind == TY_REF) printed = printed->ref->sub;
            if (Nominal(printed))
                Fail(arg->line, "aggregate printing needs the pending rendering lowering");
            Gen(arg); auto value = Temp(t); code.Set(value);
            int null = -1;
            while (t->kind == TY_REF) {
                if (null < 0) { null = (int)Local(WasmModule::I32); code.I32(0); code.Set(null); }
                auto sub = t->ref->sub;
                auto next = Temp(sub);
                code.Get(value); code.Byte(Type(t) == WasmModule::I64 ? 0x50 : 0x45); Open(0x04);
                code.I32(1); code.Set(null);
                code.Byte(0x05); code.Get(value); Load(sub); code.Set(next); Close();
                value = next; t = sub;
            }
            pieces.push_back({t, value, null, nullptr});
        }
        auto token = Local(WasmModule::I32); code.Call(beginprint); code.Set(token);
        for (auto &p : pieces) {
            if (!p.type && !p.literal) {
                code.Get(token); code.Get(p.value); code.Call(printsnapshot); continue;
            }
            if (p.literal) {
                auto offset = module.Data(p.literal->val);
                code.Get(token); code.I32((int32_t)offset); code.I32((int32_t)p.literal->val.size()); code.Call(printbytes);
                continue;
            }
            if (p.null >= 0) {
                code.Get(p.null); Open(0x04);
                auto offset = module.Data("null");
                code.Get(token); code.I32((int32_t)offset); code.I32(4); code.Call(printbytes);
                code.Byte(0x05); PrintScalar(token, p.value, p.type); Close();
            } else PrintScalar(token, p.value, p.type);
        }
        code.Get(token); code.Call(endprint);
        if (hassnapshots) {
            auto &actions = scopes.back();
            actions.erase(remove_if(actions.begin(), actions.end(), [&](const CleanupAction &action) {
                return action.snapshot != UINT32_MAX && action.memory == printid;
            }), actions.end());
        }
    }
    void CallValue(Call *c, TypeExpr *resulttype = nullptr) {
        if (c->defaultinit) { Gen(c->defaultinit); return; }
        if (c->builtin >= 0) {
            auto an = c->ValueArgNodes();
            switch ((BuiltinKind)c->builtin) {
                case B_PRINT: Print(c); return;
                case B_ASSERT:
                    Condition(an[0]); code.Byte(0x45); Open(0x04); Trap(1, c->line); Close(); return;
                case B_EXIT:
                    Gen(an[0]); code.Byte(0xa7); code.Call(exitfn); code.Byte(0x00); return;
                case B_LEN: case B_CAP: case B_PUSH: case B_POP: case B_CLEAR:
                    ArrayBuiltin(c, an, resulttype); return;
                case B_DEFAULT: {
                    auto t = resulttype ? resulttype : c->exprtype;
                    if (Aggregate(t)) Fail(c->line, "aggregate defaults need a fresh destination");
                    auto type = Type(t);
                    if (type == WasmModule::F32) code.F32(0);
                    else if (type == WasmModule::F64) code.F64(0);
                    else if (type == WasmModule::I64) code.I64(0);
                    else code.I32(0);
                    return;
                }
                default: Fail(c->line, cat("builtin ", builtindefs[c->builtin].name, " is not implemented"));
            }
        }
        if (FixedResult(ActualType(c)))
            Fail(c->line, "aggregate call results need a checked destination");
        if (c->fvbody) {
            BindCallParameters(c);
            auto wanted = resulttype ? resulttype : c->exprtype;
            BlockValue(c->fvbody, !Void(wanted), wanted); return;
        }
        if (!c->dispatch.empty()) Fail(c->line, "ADT dispatch is not implemented");
        auto it = functions.find(c->spec);
        if (it == functions.end()) Fail(c->line, "missing direct function specialization");
        auto args = c->ValueArgNodes();
        if (args.size() != c->spec->params.size()) Fail(c->line, "call parameter mismatch");
        if (any_of(c->spec->params.begin(), c->spec->params.end(),
                   [&](VarDef *parameter) { return FixedParameter(parameter->type); })) {
            auto result = c->spec->rets.empty() ? NoLocal : Temp(c->spec->rets[0]);
            vector<uint32_t> values(args.size(), NoLocal);
            FixedCallArguments(c, args, values, 0, result);
            if (result != NoLocal) {
                code.Get(result);
                Convert(c->spec->rets[0], resulttype ? resulttype : c->exprtype);
            }
            return;
        }
        for (size_t i = 0; i < args.size(); i++) {
            Gen(args[i]); Convert(args[i]->exprtype, c->spec->params[i]->type);
        }
        if (NeedsBase(c->spec)) StackIndex((uint32_t)storage.calltops.at(c));
        code.Call(it->second);
        if (!c->spec->rets.empty()) Convert(c->spec->rets[0], resulttype ? resulttype : c->exprtype);
    }
    void Gen(Node *n, TypeExpr *resulttype = nullptr) {
        if (ReadFixedTemporary(n, resulttype)) return;
        if (!resulttype && Nominal(n->exprtype))
            Fail(n->line, "aggregate values need the pending destination lowering");
        auto unary = Is<Unary>(n);
        auto arrayaddress = Is<Ident>(n) || (unary && unary->op == T_BITAND);
        if (n->exprtype && n->exprtype->kind == TY_ARRAY && !arrayaddress) {
            auto borrowed = [&](TypeExpr *type, bool explicitReference = false) {
                return type && type->kind == TY_REF && type->ref->sub->kind == TY_ARRAY &&
                       (TEq(type->ref->sub, n->exprtype) ||
                        (explicitReference && resulttype && TEq(type, resulttype)));
            };
            if (auto index = Is<Index>(n)) arrayaddress = borrowed(ArrayElement(index->obj));
            else if (auto field = Is<Dot>(n); field && field->IsField()) {
                auto actual = ActualType(field);
                while (actual->kind == TY_REF) actual = actual->ref->sub;
                arrayaddress = TEq(actual, n->exprtype);
            }
            else if (auto call = Is<Call>(n)) {
                auto &rets = call->spec ? call->spec->rets : call->rettypes;
                arrayaddress = rets.size() == 1 && borrowed(rets[0], true);
            } else if (auto inlined = Is<InlineBlock>(n))
                arrayaddress = inlined->spec->rets.size() == 1 && borrowed(inlined->spec->rets[0], true);
        }
        if (n->exprtype && n->exprtype->kind == TY_ARRAY && !Is<Ident>(n) &&
            !arrayaddress)
            Fail(n->line, "array-valued temporary results need the pending destination lowering");
        if (auto v = Is<IntLit>(n)) { code.I64(v->val); return; }
        if (auto v = Is<FltLit>(n)) {
            if (Type(n->exprtype) == WasmModule::F32) code.F32((float)v->val); else code.F64(v->val);
            return;
        }
        if (auto v = Is<BoolLit>(n)) { code.I32(v->val); return; }
        if (Is<NullLit>(n)) {
            if (ReferenceType(n) == WasmModule::I64) code.I64(0); else code.I32(0);
            return;
        }
        if (auto v = Is<Ident>(n)) {
            if (!v->vdef) Fail(n->line, "function value is not a runtime scalar");
            auto &s = Find(v->vdef);
            if (Nominal(s.type) && n->exprtype->kind == TY_REF && TEq(s.type, n->exprtype->ref->sub)) {
                ReferenceAddress(s); return;
            }
            Read(s); auto actual = s.type;
            while (actual->kind == TY_REF && n->exprtype->kind != TY_REF) {
                CheckNull(n->line, Type(actual)); actual = actual->ref->sub; Load(actual);
            }
            Convert(actual, n->exprtype); return;
        }
        if (auto v = Is<Unary>(n)) {
            if (v->op == T_BITAND) {
                if (auto field = Is<Dot>(v->child); field && field->IsField()) {
                    auto place = FieldPlace(field);
                    if (place.type->kind == TY_REF) { ReadPlace(place); Convert(place.type, n->exprtype); }
                    else if (n->exprtype->kind != TY_REF && !Aggregate(place.type)) {
                        ReadPlace(place); Convert(place.type, n->exprtype);
                    }
                    else if (place.type->kind == TY_ARRAY && n->exprtype->kind == TY_REF)
                        EmitArrayReference(ArrayFromPlace(place, n->line), n->exprtype, n->line);
                    else PlaceAddress(place, Type(n->exprtype), n->line);
                    return;
                }
                if (auto index = Is<Index>(v->child)) {
                    auto element = ElementAddress(index);
                    if (element.type->kind == TY_REF) {
                        LoadElement(element);
                        Convert(element.type, n->exprtype);
                    } else if (n->exprtype->kind != TY_REF) {
                        LoadElement(element); Convert(element.type, n->exprtype);
                    } else if (Type(n->exprtype) == WasmModule::I32) code.Byte(0xa7);
                    return;
                }
                auto id = Is<Ident>(v->child);
                if (!id && (Is<Call>(v->child) || Is<InlineBlock>(v->child)) &&
                    ActualType(v->child)->kind == TY_REF) {
                    ReferenceValue(v->child, Type(n->exprtype)); return;
                }
                if (!id && Aggregate(Operand(v->child->exprtype)))
                    Fail(n->line, "aggregate temporaries need the pending destination lowering");
                if (!id || !id->vdef) Fail(n->line, "only scalar local/global addresses are implemented");
                auto &s = Find(id->vdef);
                if (s.type->kind == TY_REF) Read(s);
                else ReferenceAddress(s);
                if (n->exprtype->kind != TY_REF) {
                    auto pointertype = s.type->kind == TY_REF ? Type(s.type)
                                      : s.type->kind == TY_ARRAY ? BorrowedArrayAddressType(s.type)
                                      : FatPointers() ? WasmModule::I64 : WasmModule::I32;
                    CheckNull(n->line, pointertype); Load(Operand(v->child->exprtype));
                }
                return;
            }
            auto t = Operand(v->child->exprtype);
            if (v->op == T_MINUS && t->kind == TY_INT) { code.I64(0); Gen(v->child); code.Byte(0x7d); Normalize(t); }
            else {
                Gen(v->child);
                if (v->op == T_MINUS) code.Byte(t->fltstorage == FS_F32 ? 0x8c : 0x9a);
                else if (v->op == T_NOT) code.Byte(Type(v->child->exprtype) == WasmModule::I64 ? 0x50 : 0x45);
                else if (v->op == T_BITNOT) { code.I64(-1); code.Byte(0x85); Normalize(t); }
                else Fail(n->line, "unsupported unary operator");
            }
            Convert(v->op == T_NOT ? ast.booltype : t, n->exprtype); return;
        }
        if (auto v = Is<Binary>(n)) { BinaryValue(v); return; }
        if (auto v = Is<Index>(n)) {
            auto element = ElementAddress(v);
            if (n->exprtype->kind != TY_REF || !TEq(n->exprtype->ref->sub, element.type)) {
                LoadElement(element); Convert(element.type, n->exprtype);
            } else if (Type(n->exprtype) == WasmModule::I32) code.Byte(0xa7);
            return;
        }
        if (auto v = Is<Dot>(n); v && v->IsField()) {
            if (n->exprtype->kind == TY_ARRAY) { code.Get(ResolveArray(n).image.address); return; }
            auto place = FieldPlace(v);
            if (n->exprtype->kind == TY_REF && TEq(n->exprtype->ref->sub, place.type)) {
                if (place.type->kind == TY_ARRAY)
                    EmitArrayReference(ArrayFromPlace(place, n->line), n->exprtype, n->line);
                else PlaceAddress(place, Type(n->exprtype), n->line);
            } else { ReadPlace(place); Convert(place.type, n->exprtype); }
            return;
        }
        if (auto v = Is<Dot>(n); v && (v->member == B_LEN || v->member == B_CAP)) {
            auto place = ResolveArray(v->obj); auto array = place.layout.type;
            if (v->member == B_LEN) ArrayLength(place);
            else if (VariableArray(array)) Fail(v->line, "variable arrays have no static capacity");
            else ArrayCapacity(place);
            return;
        }
        if (auto v = Is<AsCast>(n)) {
            Gen(v->child); Convert(Operand(v->child->exprtype), v->totype); Convert(v->totype, n->exprtype); return;
        }
        if (auto v = Is<Call>(n)) { CallValue(v, resulttype); return; }
        if (auto v = Is<Block>(n)) { BlockValue(v, !Void(n->exprtype), n->exprtype); return; }
        if (auto v = Is<IfExpr>(n)) {
            Condition(v->cond); Open(0x04, Void(n->exprtype) ? 0x40 : Type(n->exprtype));
            BlockValue(v->thenb, !Void(n->exprtype), n->exprtype);
            if (v->elseb) { code.Byte(0x05); Gen(v->elseb); if (!Void(n->exprtype) && !Void(v->elseb->exprtype)) Convert(v->elseb->exprtype, n->exprtype); if (Void(n->exprtype) && !Void(v->elseb->exprtype)) code.Byte(0x1a); }
            Close(); return;
        }
        if (auto v = Is<InlineBlock>(n)) {
            for (auto p : v->spec->params) RequireCallValue(p->type, false, n->line);
            for (auto r : v->spec->rets) RequireCallValue(r, true, n->line);
            auto ret = v->spec->rets.empty() ? nullptr : v->spec->rets[0];
            if (FixedResult(ret)) Fail(n->line, "aggregate inline results need a checked destination");
            auto result = ret ? (int)Temp(ret) : -1;
            auto label = Open();
            targets.push_back({Target::Inline, v->sf, scopes.size(), label, -1, result, ret});
            BlockValue(v->body, ret != nullptr, ret);
            if (ret && v->body->tail && !Void(v->body->tail->exprtype)) code.Set(result);
            targets.pop_back(); Close();
            if (ret) { code.Get(result); Convert(ret, resulttype ? resulttype : n->exprtype); }
            return;
        }
        if (Is<MatchExpr>(n)) Fail(n->line, "value-producing matches need the pending destination lowering");
        if (auto v = Is<LoopExpr>(n)) { Loop(v->body, nullptr, n->exprtype); return; }
        if (auto v = Is<EarlyBlock>(n)) {
            auto result = Void(n->exprtype) ? -1 : (int)Temp(n->exprtype);
            auto label = Open(); targets.push_back({Target::Early, nullptr, scopes.size(), label, -1, result, n->exprtype});
            BlockValue(v->body, result >= 0, n->exprtype);
            if (result >= 0 && v->body->tail && !Void(v->body->tail->exprtype)) code.Set(result);
            targets.pop_back(); Close(); if (result >= 0) code.Get(result); return;
        }
        Fail(n->line, "this expression is not implemented (scalar backend)");
    }
    Target FindTarget(bool cont = false) {
        for (auto it = targets.rbegin(); it != targets.rend(); ++it)
            if (it->kind == Target::Loop || (!cont && it->kind == Target::Early)) return *it;
        Fail({}, "missing checked loop target");
    }
    void Exit(Target t, Node *value) {
        if (value) {
            if (t.destination) ConstructFixed(*t.destination, value);
            else {
                Gen(value);
                if (t.result >= 0) { Convert(value->exprtype, t.type); code.Set(t.result); }
                else if (!Void(value->exprtype)) code.Byte(0x1a);
            }
        }
        Cleanup(t.scope); Branch(t.label);
    }
    void Loop(Block *body, Node *cond, TypeExpr *resulttype) {
        auto result = Void(resulttype) ? -1 : (int)Temp(resulttype);
        auto end = Open(), head = Open(0x03);
        targets.push_back({Target::Loop, nullptr, scopes.size(), end, head, result, resulttype});
        if (cond) { Condition(cond); code.Byte(0x45); Branch(end, true); }
        BlockValue(body, false); Branch(head);
        targets.pop_back(); Close(); Close(); if (result >= 0) code.Get(result);
    }
    void For(ForLoop *f) {
        if (f->iterkind != IK_RANGE && f->iterkind != IK_COUNT)
            { ArrayFor(f); return; }
        auto r = Is<RangeExpr>(f->iter);
        auto ct = f->iter->exprtype;
        auto counter = Temp(ct), high = Temp(ct);
        if (r) Gen(r->lo); else code.I64(0);
        code.Set(counter); Gen(r ? r->hi : f->iter); code.Set(high);
        if (f->idxdef) { code.I64(0); Write(Find(f->idxdef)); }
        auto end = Open(), head = Open(0x03);
        code.Get(counter); code.Get(high);
        code.Byte(IsUnsigned(ct->intstorage) ? 0x5a : 0x59); Branch(end, true);
        code.Get(counter); Convert(ct, f->vdef->type); Write(Find(f->vdef));
        auto step = Open();
        targets.push_back({Target::Loop, nullptr, scopes.size(), end, step, -1, nullptr});
        BlockValue(f->body, false);
        targets.pop_back(); Close();
        code.Get(counter); code.I64(1); code.Byte(0x7c); Normalize(ct); code.Set(counter);
        if (f->idxdef) { auto &s = Find(f->idxdef); Read(s); code.I64(1); code.Byte(0x7c); Write(s); }
        Branch(head); Close(); Close();
    }
    static TType AssignOp(TType op) {
        switch (op) {
            case T_PLUSEQ: return T_PLUS; case T_MINUSEQ: return T_MINUS;
            case T_MULEQ: return T_MUL; case T_DIVEQ: return T_DIV; case T_MODEQ: return T_MOD;
            case T_ANDEQ: return T_BITAND; case T_OREQ: return T_BITOR; case T_XOREQ: return T_XOR;
            case T_SHLEQ: return T_SHL; case T_SHREQ: return T_SHR;
            default: return op;
        }
    }
    void Assign(Node *lv, Node *rhs, TType op, bool pointee, Line line) {
        if (auto field = Is<Dot>(lv); field && field->IsField()) {
            AssignField(field, rhs, op, pointee, line); return;
        }
        if (auto index = Is<Index>(lv)) { AssignElement(index, rhs, op, pointee, line); return; }
        auto id = Is<Ident>(lv);
        if (!id || !id->vdef) Fail(line, "only scalar variable assignment is implemented");
        auto s = Find(id->vdef);
        TypeExpr *t = s.type;
        if (op == T_DOTASSIGN) {
            if (t->kind != TY_REF) Fail(line, "only scalar reference rebinding is implemented");
            if (auto source = Is<Ident>(rhs); source && source->vdef && source->vdef->type->kind != TY_REF)
                ReferenceAddress(Find(source->vdef));
            else ReferenceValue(rhs, Type(t));
            Write(s);
            return;
        }
        if (t->kind == TY_ARRAY) {
            if (!InlineArray(t)) Fail(line, "whole-array assignment needs the pending destination lowering");
            AssignFixed(OwnerPlace(id->vdef), rhs, op, line); return;
        }
        if (Nominal(t)) { AssignFixed(OwnerPlace(id->vdef), rhs, op, line); return; }
        int address = -1;
        if (pointee) {
            if (t->kind == TY_REF && (Nominal(t->ref->sub) || InlineArray(t->ref->sub))) {
                Read(s); auto destination = PointeePlace(t, line);
                AssignFixed(destination, rhs, op, line); return;
            }
            Read(s); CheckNull(line, Type(t)); address = (int)Local(Type(t)); code.Set(address);
            t = t->ref->sub;
            if (t->kind == TY_ARRAY) Fail(line, "whole-array assignment needs the pending destination lowering");
            if (Nominal(t)) Fail(line, "whole-aggregate assignment needs the pending destination lowering");
        }
        if (op != T_ASSIGN) {
            if (address >= 0) { code.Get(address); Load(t); } else Read(s);
        }
        if (rhs) { Gen(rhs); Convert(rhs->exprtype, t); }
        else if (t->kind == TY_FLT) {
            if (t->fltstorage == FS_F32) code.F32(1); else code.F64(1);
        } else code.I64(1);
        if (op != T_ASSIGN) Arithmetic(op, t, line);
        if (address >= 0) {
            auto result = Temp(t); code.Set(result); code.Get(address); code.Get(result); Store(t);
        } else Write(s);
    }
    void Statement(Node *n) {
        if (auto v = Is<VarDecl>(n)) {
            if (v->defs.size() > 1 && v->inits.size() == 1)
                Fail(n->line, "multiple-result bindings are not implemented");
            for (size_t i = 0; i < v->defs.size(); i++) {
                auto &s = Find(v->defs[i]);
                if (i >= v->inits.size()) {
                    if (s.type->kind == TY_ARRAY)
                        Fail(v->defs[i]->line, "default array construction needs the pending destination lowering");
                    continue;
                }
                if (s.type->kind == TY_ARRAY) {
                    if (v->inline_arg) {
                        RequireCallValue(s.type, false, n->line);
                        ConstructFixed(FreshOwner(v->defs[i], v), v->inits[i]); continue;
                    }
                    InitArray(v->defs[i], s, v->inits[i], v); continue;
                }
                if (Nominal(s.type)) {
                    if (v->inline_arg) RequireCallValue(s.type, false, n->line);
                    ConstructFixed(FreshOwner(v->defs[i], v), v->inits[i]); continue;
                }
                Gen(v->inits[i]); Convert(v->inits[i]->exprtype, s.type); Write(s);
            }
            return;
        }
        if (auto v = Is<goose::Assign>(n)) { Assign(v->lval, v->rhs, AssignOp(v->op), v->pointee, n->line); return; }
        if (auto v = Is<IncDec>(n)) { Assign(v->lval, nullptr, v->op == T_INC ? T_PLUS : T_MINUS,
                                                   v->lval->exprtype->kind == TY_REF, n->line); return; }
        if (auto v = Is<Return>(n)) {
            if (v->vals.size() > 1) Fail(n->line, "multiple results are not implemented");
            for (auto it = targets.rbegin(); it != targets.rend(); ++it)
                if ((it->kind == Target::Function || it->kind == Target::Inline) && it->sf == v->target) {
                    Exit(*it, v->vals.empty() ? nullptr : v->vals[0]); return;
                }
            Fail(n->line, "nonlocal return across a Wasm call requires the pending exception lowering");
        }
        if (auto v = Is<Break>(n)) { Exit(FindTarget(), v->val); return; }
        if (Is<Continue>(n)) { auto t = FindTarget(true); Cleanup(t.scope); Branch(t.cont); return; }
        if (auto v = Is<Defer>(n)) { assert(!scopes.empty()); scopes.back().push_back({v}); return; }
        if (auto v = Is<While>(n)) { Loop(v->body, v->cond, nullptr); return; }
        if (auto v = Is<ForLoop>(n)) { For(v); return; }
        if (auto match = Is<MatchExpr>(n)) { EnumMatchStatement(match); return; }
        if (Is<FnDecl>(n)) return;
        auto unary = Is<Unary>(n);
        if (FixedBinary(n) || (unary && unary->op == T_MINUS && FixedResult(ActualType(n)))) {
            WithFixedTemporary(ActualType(n), n, [&](const FixedPlace &) {}); return;
        }
        // Discard the declared reference result without reading its struct.
        auto call = Is<Call>(n);
        if (call || Is<InlineBlock>(n)) {
            auto actual = ActualType(n);
            if (FixedResult(actual) && (!call || call->builtin < 0)) {
                WithFixedTemporary(actual, n, [&](const FixedPlace &) {}); return;
            }
            if (Nominal(n->exprtype) && actual && actual->kind == TY_REF) {
                Gen(n, actual); code.Byte(0x1a); return;
            }
        }
        Gen(n); if (!Void(n->exprtype)) code.Byte(0x1a);
    }
    void StartFunction(uint32_t index, FnSpec *sp) {
        fn = index; current = sp; code.bytes.clear(); slots.clear(); addressed.clear();
        targets.clear(); scopes.clear(); labels.clear(); framesize = 0;
        fixedoffsetscratch = UINT32_MAX;
        fixedfillitems.fill(UINT32_MAX); fixedfillposition = fixedfillbase = UINT32_MAX;
        arraystorevalue = UINT32_MAX; fixedpushscratch.fill(nullopt);
    }
    void EndFunction() {
        assert(labels.empty() && scopes.empty() && targets.empty());
        module.functions[fn - module.imports.size()].code = std::move(code);
    }
    void EmitFloatToInt() {
        StartFunction(f2ifn, nullptr);
        // As in the native gs_f2iwrap fast path: ordered comparisons exclude
        // NaN and guard trunc_f64_s's exact nontrapping interval. Other values
        // retain the existing modulo-2^64 host conversion.
        code.Get(0); code.F64(-0x1p63); code.Byte(0x66); // f64.ge
        code.Get(0); code.F64(0x1p63); code.Byte(0x63);  // f64.lt
        code.Byte(0x71); // i32.and
        Open(0x04, WasmModule::I64);
        code.Get(0); code.Byte(0xb0); // i64.trunc_f64_s
        code.Byte(0x05); code.Get(0); code.Call(f2islowfn);
        Close();
        EndFunction();
    }
    void EmitReserve() {
        StartFunction(reservefn, nullptr);
        auto old = Local(WasmModule::I32), end = Local(WasmModule::I64), pages = Local(WasmModule::I32);
        code.Byte(0x23); code.U(0); code.Tee(old); code.Byte(0xad);
        code.Get(0); code.Byte(0xad); code.Byte(0x7c); code.Tee(end);
        code.I64(UINT32_MAX); code.Byte(0x56); Open(0x04); Trap(5, {}); Close();
        code.Get(end); code.I64(65535); code.Byte(0x7c); code.I64(16); code.Byte(0x88); code.Byte(0xa7); code.Tee(pages);
        code.Byte(0x3f); code.U(0); code.Byte(0x4b); Open(0x04);
        code.Get(pages); code.Byte(0x3f); code.U(0); code.Byte(0x6b);
        code.Byte(0x40); code.U(0); code.I32(-1); code.Byte(0x46);
        Open(0x04); Trap(5, {}); Close(); Close();
        code.Get(end); code.Byte(0xa7); code.Byte(0x24); code.U(0); code.Get(old);
        EndFunction();
    }
    void EmitSpec(FnSpec *sp) {
        StartFunction(functions.at(sp), sp);
        Scan(sp->body);
        framebase = Local(WasmModule::I32);
        for (size_t i = 0; i < sp->params.size(); i++) Bind(sp->params[i], (uint32_t)i);
        BindTree(sp->body);
        if (framesize) {
            code.I32((int32_t)framesize); code.Call(reservefn); code.Set(framebase);
            for (size_t i = 0; i < sp->params.size(); i++) {
                auto &s = Find(sp->params[i]);
                if (FixedParameter(s.type)) {
                    auto plan = storage.fixedvalues.find(sp->params[i]);
                    if (plan == storage.fixedvalues.end() ||
                        plan->second.origin != WasmStoragePlan::FixedOrigin::Parameter ||
                        plan->second.function != sp || !plan->second.argument || !plan->second.initialized)
                        Fail(sp->params[i]->line, "aggregate parameter needs its planned function owner");
                    CopyBytes(OwnerPlace(sp->params[i]),
                              {s.type, (uint32_t)i, 0, 0, false, true},
                              plan->second.image, sp->params[i]->line, true);
                } else if (s.memory) { Address(s); code.Get((uint32_t)i); StoreFixed(s.type); }
            }
        }
        auto ret = sp->rets.empty() ? nullptr : sp->rets[0];
        auto fixed = FixedResult(ret);
        auto result = ret && !fixed ? (int)Temp(ret) : -1;
        FreshFixedDestination destination {};
        if (fixed) {
            auto image = RequireFixed(ret, sp->sf->line);
            destination = {{ret, FixedResultParameter(sp), 0, 0, false, true}, nullptr, 0, image,
                           FreshFixedOrigin::IncomingResult, sp->body, std::max(1u, image)};
        }
        auto end = Open();
        targets.push_back({Target::Function, sp->sf, 0, end, -1, result, ret, fixed ? &destination : nullptr});
        if (fixed) BlockInto(sp->body, destination);
        else {
            BlockValue(sp->body, ret != nullptr, ret);
            if (ret && sp->body->tail && !Void(sp->body->tail->exprtype)) code.Set(result);
        }
        targets.pop_back(); Close();
        if (framesize) { code.Get(framebase); code.Byte(0x24); code.U(0); }
        if (ret && !fixed) code.Get(result);
        EndFunction();
    }
    string Run() {
        storage.Build([&](Line l, const string &message) { Fail(l, message); },
                      [&](TypeExpr *t, Line line) { return RequireFixed(t, line); });
        module.memories = storage.Memories();
        // Imports are versioned as a group. The adapter rejects reentry and runs
        // one program per instance. There is no implicit native extern bridge.
        beginprint = module.ImportFn("print_begin_v1", {}, {WasmModule::I32});
        printint = module.ImportFn("print_int_v1", {WasmModule::I32, WasmModule::I64, WasmModule::I32}, {});
        printfloat = module.ImportFn("print_float_v1", {WasmModule::I32, WasmModule::F64, WasmModule::I32}, {});
        printbool = module.ImportFn("print_bool_v1", {WasmModule::I32, WasmModule::I32}, {});
        printbytes = module.ImportFn("print_bytes_v1", {WasmModule::I32, WasmModule::I32, WasmModule::I32}, {});
        endprint = module.ImportFn("print_end_v1", {WasmModule::I32}, {});
        failfn = module.ImportFn("fail_v1", {WasmModule::I32, WasmModule::I32, WasmModule::I32, WasmModule::I32}, {});
        exitfn = module.ImportFn("exit_v1", {WasmModule::I32}, {});
        fmodfn = module.ImportFn("fmod_v1", {WasmModule::F64, WasmModule::F64}, {WasmModule::F64});
        f2islowfn = module.ImportFn("float_to_int_v1", {WasmModule::F64}, {WasmModule::I64});
        if (storage.byteprints) {
            snapshotbytes = module.ImportFn("snapshot_memory_bytes_v1",
                                           {WasmModule::I32, WasmModule::I32, WasmModule::I32}, {WasmModule::I32});
            printsnapshot = module.ImportFn("print_snapshot_v1", {WasmModule::I32, WasmModule::I32}, {});
            dropsnapshot = module.ImportFn("drop_snapshot_v1", {WasmModule::I32}, {});
        }
        if (FatPointers()) memories.emplace(module, failfn);
        reservefn = module.AddFn("goose.reserve_frame", {WasmModule::I32}, {WasmModule::I32});
        for (auto sp : ast.fnspecs) if (sp->live) {
            if (sp->sf->isextern) Fail(sp->sf->line, "native extern functions need an explicit Wasm host adapter");
            if (sp->sf->isexport) Fail(sp->sf->line, "exported C interfaces need an explicit Wasm host adapter");
            if (sp->sf->isthread) Fail(sp->sf->line, "workers need the pending isolated-instance adapter");
            if (sp->rets.size() > 1) Fail(sp->sf->line, "multiple results are not implemented");
            vector<uint8_t> args, rets;
            for (auto p : sp->params) {
                RequireCallValue(p->type, false, p->line);
                args.push_back(FixedParameter(p->type) ? WasmModule::I32 : Type(p->type));
            }
            for (auto r : sp->rets) {
                RequireCallValue(r, true, r->line);
                if (!FixedResult(r)) rets.push_back(Type(r));
            }
            if (NeedsBase(sp)) args.push_back(WasmModule::I32);
            if (!sp->rets.empty() && FixedResult(sp->rets[0])) args.push_back(WasmModule::I32);
            functions[sp] = module.AddFn(cat(sp->sf->qname, ".", sp->id), args, rets);
        }
        initfn = module.AddFn("goose.init", {}, {});
        startfn = module.AddFn("goose.start", {}, {});
        for (auto g : ast.globals) for (auto v : g->defs) {
            if (!Nominal(v->type)) Type(v->type);
            auto bytes = DataArray(v->type) ? 8u : std::max(1u, Size(v->type));
            auto offset = InlineArray(v->type) || Nominal(v->type)
                            ? module.ZeroData(bytes) : module.Data(string(bytes, '\0'));
            globals[v] = {v->type, 0, offset, true, true};
        }
        EmitReserve();
        for (auto sp : ast.fnspecs) if (sp->live) EmitSpec(sp);
        StartFunction(initfn, nullptr);
        // Initializers can contain inlined scalar calls with local bindings.
        for (auto g : ast.globals) { Scan(g); BindTree(g); }
        framebase = Local(WasmModule::I32);
        if (framesize) { code.I32((int32_t)framesize); code.Call(reservefn); code.Set(framebase); }
        for (auto g : ast.globals) Statement(g);
        if (framesize) { code.Get(framebase); code.Byte(0x24); code.U(0); }
        EndFunction();
        StartFunction(startfn, nullptr);
        code.Call(initfn);
        auto main = ast.MainFunction();
        if (main && !main->specs.empty()) {
            auto sp = main->specs[0];
            if (NeedsBase(sp)) code.I32(0);
            code.Call(functions.at(sp));
            for (auto r : sp->rets) { (void)r; code.Byte(0x1a); }
        }
        EndFunction();
        if (f2ifn != UINT32_MAX) EmitFloatToInt();
        module.exports.push_back({"memory", 2, 0});
        for (uint32_t i = 1; i < module.memories; i++)
            module.exports.push_back({cat("data_memory_", i), 2, i});
        module.exports.push_back({"_start", 0, startfn});
        return module.Finish();
    }

    TypeExpr *ActualType(Node *n);
    using FixedReadConsumer = void (*)(void *, const FixedPlace &);
    bool HasFixedTemporary(Node *n);
    Binary *FixedBinary(Node *n);
    bool FixedOperandEffects(Node *n, int &budget);
    bool CanCopyFixedArray(TypeExpr *to, TypeExpr *from);
    FreshFixedDestination FixedMathDestination(FreshFixedDestination fresh, TypeExpr *type, Line line);
    void BinaryFixedInto(FixedPlace destination, FixedMathOperand left, FixedMathOperand right,
                         TType op, Line line);
    void ConstructFixedBinary(FreshFixedDestination fresh, Binary *source);
    void WithReadPlace(Node *n, void *context, FixedReadConsumer consume);
    template<class Consume> void WithReadPlace(Node *n, Consume consume);
    bool ReadFixedTemporary(Node *n, TypeExpr *resulttype);
    FixedPlace OwnerPlace(VarDef *owner);
    FreshFixedDestination FreshOwner(VarDef *owner, Node *initialization);
    FreshFixedDestination FreshCallParameter(Call *call, size_t position);
    uint32_t FixedResultParameter(FnSpec *function);
    void BindCallParameters(Call *call);
    void BlockInto(Block *body, FreshFixedDestination destination);
    void CallInto(FreshFixedDestination destination, Node *expression);
    void FixedCallArguments(Call *call, const vector<Node *> &arguments,
                            vector<uint32_t> &values, size_t position, uint32_t result,
                            uint32_t destination = NoLocal);
    FreshDataArrayDestination ReserveFreshDataArray(VarDef *owner, const Slot &slot,
                                                  VarDecl *initialization, uint32_t count,
                                                  uint32_t literalCount = NoLocal);
    FreshFixedDestination FreshDataElement(const FreshDataArrayDestination &destination,
                                          uint32_t ordinal, Line line);
    ArrayPlace FreshArrayPlace(const FreshFixedDestination &destination, Line line);
    FreshFixedDestination FixedChild(FreshFixedDestination parent, TypeExpr *type, uint32_t offset, Line line);
    FixedFields FieldsOf(TypeExpr *type, Line line);
    FixedFields VariantFields(EnumInst *instance, int variant, Line line);
    pair<TypeExpr *, uint32_t> StoredField(TypeExpr *type, int field, Line line);
    void ConstructFields(FreshFixedDestination destination, StructLit *literal, const FixedFields &fields,
                         uint32_t prefix, Line line);
    void ConstructAggregateArray(FreshFixedDestination destination, ArrayLit *literal);
    void ConstructRepeatedAggregate(FreshFixedDestination destination, Node *value,
                                    uint64_t count, bool each);
    void CopyFixed(FreshFixedDestination destination, FixedPlace source, Line line);
    TypeExpr *FreshRootType(const FreshFixedDestination &destination);
    bool IsFreshWholeOwner(const FreshFixedDestination &destination);
    void CheckFreshDestination(const FreshFixedDestination &destination, Line line);
    template<class Construct, class Consume>
    void WithFixedValue(TypeExpr *type, Node *expression, Construct construct, Consume consume);
    template<class Consume> void WithFixedTemporary(TypeExpr *type, Node *expression, Consume consume);
    void AssignFixed(FixedPlace destination, Node *source, TType op, Line line);
    void CompoundFixed(FixedPlace destination, Node *source, TType op, Line line);
    void EnumMatchStatement(MatchExpr *match);
    FixedPlace ResolvePlace(Node *n);
    FixedPlace FieldPlace(Dot *field);
    FixedPlace FieldPlace(Dot *field, FixedPlace object);
    FixedPlace PointeePlace(TypeExpr *reference, Line line);
    FixedPlace DereferencePlace(FixedPlace place, Line line);
    void PlaceAddress(const FixedPlace &place, uint8_t representation, Line line);
    void ReadPlace(const FixedPlace &place);
    void StorePlace(const FixedPlace &place);
    void StoreAddress(const FixedPlace &place);
    void ConstructFixed(FreshFixedDestination destination, Node *source);
    void NegateFixedInto(FixedPlace destination, FixedPlace source, Line line);
    bool ExitingFixedInitializer(Node *source);
    void AssignField(Dot *field, Node *rhs, TType op, bool pointee, Line line);
    bool FieldPath(Node *n);
    TypeExpr *ArrayType(Node *n);
    TypeExpr *ArrayElement(Node *n);
    // Private Gen/Convert transport only. Array call values remain guarded.
    uint8_t BorrowedArrayAddressType(TypeExpr *array) {
        return DataArray(array) || (InlineArray(array) && FatPointers())
                   ? WasmModule::I64 : WasmModule::I32;
    }
    ArrayLayoutFacts ArrayLayout(TypeExpr *array, Line line);
    ArrayPlace ArrayFromPlace(FixedPlace image, Line line);
    ArrayPlace ArrayOwner(VarDef *owner, FixedPlace image, Line line);
    ArrayPlace FrameArrayOwner(VarDef *owner, const Slot &slot, Line line);
    int ArrayAllocationMemory(VarDef *owner, const Slot *slot, const FixedPlace *destination, Line line);
    ArrayPlace CaptureArrayBorrow(TypeExpr *array, uint32_t value, uint8_t representation,
                                  ArrayOrigin origin, Line line);
    ArrayPlace RefineArrayOwner(ArrayPlace place, Node *n);
    ArrayPlace ResolveArray(Node *n);
    ArrayPlace ArrayFromReference(TypeExpr *reference, uint32_t value, Line line);
    ArrayView CaptureArrayView(const ArrayPlace &place, uint32_t length, uint32_t prefix = NoLocal);
    void ViewLength(const ArrayView &view);
    void LoadArrayField(const ArrayPlace &place, uint32_t offset);
    void PrepareArrayFieldStore(const ArrayPlace &place, uint32_t offset);
    void StoreArrayField(const ArrayPlace &place, uint32_t offset);
    void ArrayLength(const ArrayPlace &place, int prefix = -1);
    void ArrayCapacity(const ArrayPlace &place);
    void PrepareArrayLengthStore(const ArrayPlace &place);
    void StoreArrayLength(const ArrayPlace &place);
    void InitArrayCount(const ArrayPlace &place, uint64_t count);
    void EmitKnownOffset(const FixedPlace &place, uint32_t memory, Line line);
    void EmitPackedAddress(const FixedPlace &place, Line line);
    void EmitMemoryZeroReference(const FixedPlace &place, Line line);
    void EmitArrayReference(const ArrayPlace &place, TypeExpr *reference, Line line);
    void InitArray(VarDef *owner, const Slot &slot, Node *init, VarDecl *declaration);
    void InitArrayCopy(VarDef *owner, const Slot &slot, Node *source);
    bool InitFixedArrayValue(VarDef *owner, const Slot &slot, Node *source);
    void CopyBytes(const FixedPlace &destination, const FixedPlace &source, uint32_t bytes,
                   Line line, bool immediate = false);
    void ZeroFixed(const FixedPlace &destination, uint32_t bytes, Line line);
    void InitFilledArray(VarDef *owner, const Slot *slot, ArrayLit *literal,
                         const FreshFixedDestination *fresh = nullptr);
    void InitByteString(VarDef *owner, const Slot *slot, StrLit *literal,
                        const FreshFixedDestination *fresh = nullptr);
    void InlineArrayLiteral(const ArrayPlace &place, ArrayLit *literal, bool reuse = false);
    void InitDataArray(VarDef *owner, const Slot &slot, ArrayLit *literal);
    void InitAggregateDataArray(VarDef *owner, const Slot &slot, VarDecl *declaration,
                                Node *source);
    void InitLimitedCapacity(VarDef *owner, const Slot &slot, ArrayLit *literal);
    void PushArray(const ArrayPlace &place, Node *value, TypeExpr *result, Line line,
                   PushScratch *scratch = nullptr);
    void ArrayBuiltin(Call *call, const vector<Node *> &arguments, TypeExpr *resulttype = nullptr);
    void ArrayEquality(Binary *node);
    ElementPlace ElementAddress(Index *index);
    ElementPlace ElementAddress(Index *index, const ArrayPlace &place);
    FixedPlace CaptureElementPlace(const ElementPlace &element);
    void ElementOffset(const ArrayView &view, uint32_t index, Line line, PushScratch *scratch = nullptr);
    void LoadElement(const ElementPlace &element);
    void StoreElement(const ElementPlace &element);
    void AssignElement(Index *index, Node *rhs, TType op, bool pointee, Line line);
    struct ArrayWalkStep { Index *node; uint32_t position, length = NoLocal; };
    struct ArrayWalk {
        Node *root = nullptr;
        optional<ArrayPlace> captured;
        vector<ArrayWalkStep> steps;
    };
    bool ArrayPathHasStatements(Node *n);
    void CaptureArrayWalk(Node *n, ArrayWalk &walk);
    ArrayPlace LoadArrayWalk(const ArrayWalk &walk);
    struct PlaceWalkStep { Node *node; uint32_t position = NoLocal, length = NoLocal; };
    struct PlaceWalk {
        Node *root = nullptr;
        optional<FixedPlace> captured;
        vector<PlaceWalkStep> steps;
    };
    void CapturePlaceWalk(Node *n, PlaceWalk &walk);
    FixedPlace LoadPlaceWalk(const PlaceWalk &walk);
    void ArrayFor(ForLoop *loop);
};

}  // namespace goose
