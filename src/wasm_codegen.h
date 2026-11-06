// Goose compiler: native scalar WebAssembly lowering. Reads the checked AST;
// it never calls CodeGen or emits C. Compound layouts await shared storage IR.
#pragma once

namespace goose {

struct WasmCodeGen {
    Ast &ast;
    WasmModule module;
    WasmBytes code;
    FnSpec *current = nullptr;
    uint32_t fn = 0;
    uint32_t framebase = 0, framesize = 0;
    uint32_t reservefn, initfn, startfn;
    uint32_t beginprint, printint, printfloat, printbool, printbytes, endprint;
    uint32_t failfn, exitfn, fmodfn, f2islowfn;
    uint32_t f2ifn = UINT32_MAX;
    struct Slot { TypeExpr *type; uint32_t local = 0, offset = 0; bool memory = false, global = false; };
    unordered_map<VarDef *, Slot> globals, slots;
    unordered_map<FnSpec *, uint32_t> functions;
    set<VarDef *> addressed;
    vector<vector<Defer *>> scopes;
    struct Target {
        enum Kind { Function, Inline, Loop, Early } kind;
        SFunction *sf = nullptr;
        size_t scope = 0;
        int label = 0, cont = -1;
        int result = -1;
        TypeExpr *type = nullptr;
    };
    vector<Target> targets;
    vector<int> labels;
    int nextlabel = 0;

    explicit WasmCodeGen(Ast &a) : ast(a) {}
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
                Type(t->ref->sub); // Only scalar frame/global pointees have Memory 0 identity.
                return WasmModule::I32;
            default: Fail(t->line, "this value layout is not implemented (scalar backend)");
        }
    }
    uint32_t Size(TypeExpr *t) {
        switch (t->kind) {
            case TY_BOOL: return 1;
            case TY_INT: return (uint32_t)IntBits(t->intstorage) / 8;
            case TY_FLT: return t->fltstorage == FS_F32 ? 4 : 8;
            case TY_REF: return 8; // Packed storage width stays independent of SSA pointer width.
            default: Type(t); return 0;
        }
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
    void CheckNull(Line l) {
        auto p = Local(WasmModule::I32);
        code.Tee(p); code.Byte(0x45); Open(0x04); Trap(4, l); Close(); code.Get(p);
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
        if (!to || from == to) return;
        while (from->kind == TY_REF && to->kind != TY_REF) {
            CheckNull(from->line); from = from->ref->sub; Load(from);
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
    void Load(TypeExpr *t) {
        switch (t->kind) {
            case TY_BOOL: code.Mem(0x2d); break;
            case TY_INT: {
                auto bits = IntBits(t->intstorage);
                auto uns = IsUnsigned(t->intstorage);
                code.Mem(bits == 64 ? 0x29 : bits == 32 ? (uns ? 0x35 : 0x34)
                                  : bits == 16 ? (uns ? 0x33 : 0x32) : (uns ? 0x31 : 0x30));
                break;
            }
            case TY_FLT: code.Mem(t->fltstorage == FS_F32 ? 0x2a : 0x2b); break;
            case TY_REF: code.Mem(0x29); code.Byte(0xa7); break;
            default: Type(t);
        }
    }
    void Store(TypeExpr *t) {
        switch (t->kind) {
            case TY_BOOL: code.Mem(0x3a); break;
            case TY_INT: {
                auto bits = IntBits(t->intstorage);
                code.Mem(bits == 64 ? 0x37 : bits == 32 ? 0x3e : bits == 16 ? 0x3d : 0x3c);
                break;
            }
            case TY_FLT: code.Mem(t->fltstorage == FS_F32 ? 0x38 : 0x39); break;
            case TY_REF: code.Byte(0xad); code.Mem(0x37); break;
            default: Type(t);
        }
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
        if (s.memory) { Address(s); Load(s.type); }
        else code.Get(s.local);
    }
    void Write(const Slot &s) {
        if (s.memory) {
            auto temp = Temp(s.type); code.Set(temp); Address(s); code.Get(temp); Store(s.type);
        } else code.Set(s.local);
    }
    void Bind(VarDef *v, optional<uint32_t> param = {}) {
        if (v->isglobal || slots.count(v)) return;
        auto t = Type(v->type);
        Slot s {v->type};
        if (addressed.count(v)) {
            s.memory = true;
            s.offset = framesize;
            if (framesize > UINT32_MAX - Size(v->type)) Fail(v->line, "frame exceeds memory32");
            framesize += Size(v->type);
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
        n->Children([&](Node *ch) { Scan(ch); });
    }
    void BindTree(Node *n) {
        if (!n || Is<FnDecl>(n)) return;
        if (auto v = Is<VarDecl>(n)) for (auto d : v->defs) Bind(d);
        if (auto f = Is<ForLoop>(n)) { Bind(f->vdef); if (f->idxdef) Bind(f->idxdef); }
        if (auto c = Is<Call>(n); c && c->fvbody)
            for (auto v : c->fvparams) Bind(v);
        n->Children([&](Node *ch) { BindTree(ch); });
    }
    void Cleanup(size_t bottom) {
        // Copy each list. Emitting a deferred body opens scopes of its own.
        for (size_t i = scopes.size(); i > bottom; i--) {
            auto list = scopes[i - 1];
            for (auto it = list.rbegin(); it != list.rend(); ++it) BlockValue((*it)->body, false);
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
        if (n->exprtype->kind == TY_REF) { code.Byte(0x45); code.Byte(0x45); }
    }
    void ReferenceValue(Node *n) {
        if (Is<NullLit>(n)) { code.I32(0); return; }
        // Narrowing can give an optional identifier its pointee's exprtype.
        // Identity and null tests still read the stored reference itself.
        if (auto id = Is<Ident>(n); id && id->vdef && id->vdef->type->kind == TY_REF) {
            Read(Find(id->vdef)); return;
        }
        if (!n->exprtype || n->exprtype->kind != TY_REF)
            Fail(n->line, "reference identity requires an address value");
        Gen(n);
    }
    void BinaryValue(Binary *n) {
        auto op = n->op;
        auto identity = op == T_DOTEQ || op == T_DOTNEQ;
        auto nulltest = (op == T_EQ || op == T_NEQ) && (Is<NullLit>(n->left) || Is<NullLit>(n->right));
        if (identity || nulltest) {
            ReferenceValue(n->left); ReferenceValue(n->right);
            code.Byte(op == T_EQ || op == T_DOTEQ ? 0x46 : 0x47);
            return;
        }
        if (n->op == T_ANDAND || n->op == T_OROR) {
            Gen(n->left); Open(0x04, WasmModule::I32);
            if (n->op == T_ANDAND) Truth(n->right); else code.I32(1);
            code.Byte(0x05);
            if (n->op == T_OROR) Truth(n->right); else code.I32(0);
            Close(); return;
        }
        auto t = Operand(n->left->exprtype);
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
    void Print(Call *c) {
        if (!c->fmtspecs.empty()) Fail(c->line, "custom formatting is not implemented");
        struct Piece { TypeExpr *type = nullptr; uint32_t value = 0; int null = -1; StrLit *literal = nullptr; };
        vector<Piece> pieces;
        // Snapshot scalar arguments before opening a host line. A return in
        // any argument must leave no host buffer behind. References are read
        // now too, before a later argument can mutate their pointees.
        for (auto arg : c->ValueArgNodes()) {
            if (auto literal = Is<StrLit>(arg)) { pieces.push_back({nullptr, 0, -1, literal}); continue; }
            auto t = arg->exprtype;
            Gen(arg); auto value = Temp(t); code.Set(value);
            int null = -1;
            while (t->kind == TY_REF) {
                if (null < 0) { null = (int)Local(WasmModule::I32); code.I32(0); code.Set(null); }
                auto sub = t->ref->sub;
                auto next = Temp(sub);
                code.Get(value); code.Byte(0x45); Open(0x04);
                code.I32(1); code.Set(null);
                code.Byte(0x05); code.Get(value); Load(sub); code.Set(next); Close();
                value = next; t = sub;
            }
            pieces.push_back({t, value, null, nullptr});
        }
        auto token = Local(WasmModule::I32); code.Call(beginprint); code.Set(token);
        for (auto &p : pieces) {
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
    }
    void CallValue(Call *c) {
        if (c->defaultinit) { Gen(c->defaultinit); return; }
        if (c->builtin >= 0) {
            auto an = c->ValueArgNodes();
            switch ((BuiltinKind)c->builtin) {
                case B_PRINT: Print(c); return;
                case B_ASSERT:
                    Gen(an[0]); code.Byte(0x45); Open(0x04); Trap(1, c->line); Close(); return;
                case B_EXIT:
                    Gen(an[0]); code.Byte(0xa7); code.Call(exitfn); code.Byte(0x00); return;
                default: Fail(c->line, cat("builtin ", builtindefs[c->builtin].name, " is not implemented"));
            }
        }
        if (c->fvbody) {
            auto args = c->ValueArgNodes();
            if (args.size() != c->fvparams.size()) Fail(c->line, "function-value parameter mismatch");
            for (size_t i = 0; i < args.size(); i++) {
                Gen(args[i]); Convert(args[i]->exprtype, c->fvparams[i]->type); Write(Find(c->fvparams[i]));
            }
            BlockValue(c->fvbody, !Void(c->exprtype), c->exprtype); return;
        }
        if (!c->dispatch.empty()) Fail(c->line, "ADT dispatch is not implemented");
        auto it = functions.find(c->spec);
        if (it == functions.end()) Fail(c->line, "missing direct function specialization");
        auto args = c->ValueArgNodes();
        if (args.size() != c->spec->params.size()) Fail(c->line, "call parameter mismatch");
        for (size_t i = 0; i < args.size(); i++) {
            Gen(args[i]); Convert(args[i]->exprtype, c->spec->params[i]->type);
        }
        code.Call(it->second);
        if (!c->spec->rets.empty()) Convert(c->spec->rets[0], c->exprtype);
    }
    void Gen(Node *n) {
        if (auto v = Is<IntLit>(n)) { code.I64(v->val); return; }
        if (auto v = Is<FltLit>(n)) {
            if (Type(n->exprtype) == WasmModule::F32) code.F32((float)v->val); else code.F64(v->val);
            return;
        }
        if (auto v = Is<BoolLit>(n)) { code.I32(v->val); return; }
        if (Is<NullLit>(n)) { code.I32(0); return; }
        if (auto v = Is<Ident>(n)) {
            if (!v->vdef) Fail(n->line, "function value is not a runtime scalar");
            auto &s = Find(v->vdef); Read(s); auto actual = s.type;
            while (actual->kind == TY_REF && n->exprtype->kind != TY_REF) {
                CheckNull(n->line); actual = actual->ref->sub; Load(actual);
            }
            Convert(actual, n->exprtype); return;
        }
        if (auto v = Is<Unary>(n)) {
            if (v->op == T_BITAND) {
                auto id = Is<Ident>(v->child);
                if (!id || !id->vdef) Fail(n->line, "only scalar local/global addresses are implemented");
                auto &s = Find(id->vdef);
                if (s.type->kind == TY_REF) Read(s); else Address(s);
                if (n->exprtype->kind != TY_REF) { CheckNull(n->line); Load(Operand(v->child->exprtype)); }
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
        if (auto v = Is<AsCast>(n)) {
            Gen(v->child); Convert(Operand(v->child->exprtype), v->totype); Convert(v->totype, n->exprtype); return;
        }
        if (auto v = Is<Call>(n)) { CallValue(v); return; }
        if (auto v = Is<Block>(n)) { BlockValue(v, !Void(n->exprtype), n->exprtype); return; }
        if (auto v = Is<IfExpr>(n)) {
            Gen(v->cond); Open(0x04, Void(n->exprtype) ? 0x40 : Type(n->exprtype));
            BlockValue(v->thenb, !Void(n->exprtype), n->exprtype);
            if (v->elseb) { code.Byte(0x05); Gen(v->elseb); if (!Void(n->exprtype) && !Void(v->elseb->exprtype)) Convert(v->elseb->exprtype, n->exprtype); if (Void(n->exprtype) && !Void(v->elseb->exprtype)) code.Byte(0x1a); }
            Close(); return;
        }
        if (auto v = Is<InlineBlock>(n)) {
            auto ret = v->spec->rets.empty() ? nullptr : v->spec->rets[0];
            auto result = ret ? (int)Temp(ret) : -1;
            auto label = Open();
            targets.push_back({Target::Inline, v->sf, scopes.size(), label, -1, result, ret});
            BlockValue(v->body, ret != nullptr, ret);
            if (ret && v->body->tail && !Void(v->body->tail->exprtype)) code.Set(result);
            targets.pop_back(); Close();
            if (ret) { code.Get(result); Convert(ret, n->exprtype); }
            return;
        }
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
            Gen(value);
            if (t.result >= 0) { Convert(value->exprtype, t.type); code.Set(t.result); }
            else if (!Void(value->exprtype)) code.Byte(0x1a);
        }
        Cleanup(t.scope); Branch(t.label);
    }
    void Loop(Block *body, Node *cond, TypeExpr *resulttype) {
        auto result = Void(resulttype) ? -1 : (int)Temp(resulttype);
        auto end = Open(), head = Open(0x03);
        targets.push_back({Target::Loop, nullptr, scopes.size(), end, head, result, resulttype});
        if (cond) { Gen(cond); code.Byte(0x45); Branch(end, true); }
        BlockValue(body, false); Branch(head);
        targets.pop_back(); Close(); Close(); if (result >= 0) code.Get(result);
    }
    void For(ForLoop *f) {
        if (f->iterkind != IK_RANGE && f->iterkind != IK_COUNT)
            Fail(f->line, "array iteration is not implemented");
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
        auto id = Is<Ident>(lv);
        if (!id || !id->vdef) Fail(line, "only scalar variable assignment is implemented");
        auto s = Find(id->vdef);
        TypeExpr *t = s.type;
        if (op == T_DOTASSIGN) {
            if (t->kind != TY_REF) Fail(line, "only scalar reference rebinding is implemented");
            if (auto source = Is<Ident>(rhs); source && source->vdef && source->vdef->type->kind != TY_REF)
                Address(Find(source->vdef));
            else ReferenceValue(rhs);
            Write(s);
            return;
        }
        int address = -1;
        if (pointee) {
            Read(s); CheckNull(line); address = (int)Local(WasmModule::I32); code.Set(address);
            t = t->ref->sub;
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
            for (size_t i = 0; i < v->defs.size(); i++) if (i < v->inits.size()) {
                auto &s = Find(v->defs[i]); Gen(v->inits[i]); Convert(v->inits[i]->exprtype, s.type); Write(s);
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
        if (auto v = Is<Defer>(n)) { assert(!scopes.empty()); scopes.back().push_back(v); return; }
        if (auto v = Is<While>(n)) { Loop(v->body, v->cond, nullptr); return; }
        if (auto v = Is<ForLoop>(n)) { For(v); return; }
        if (Is<FnDecl>(n)) return;
        Gen(n); if (!Void(n->exprtype)) code.Byte(0x1a);
    }
    void StartFunction(uint32_t index, FnSpec *sp) {
        fn = index; current = sp; code.bytes.clear(); slots.clear(); addressed.clear();
        targets.clear(); scopes.clear(); labels.clear(); framesize = 0;
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
                if (s.memory) { Address(s); code.Get((uint32_t)i); Store(s.type); }
            }
        }
        auto ret = sp->rets.empty() ? nullptr : sp->rets[0];
        auto result = ret ? (int)Temp(ret) : -1;
        auto end = Open(); targets.push_back({Target::Function, sp->sf, 0, end, -1, result, ret});
        BlockValue(sp->body, ret != nullptr, ret);
        if (ret && sp->body->tail && !Void(sp->body->tail->exprtype)) code.Set(result);
        targets.pop_back(); Close();
        if (framesize) { code.Get(framebase); code.Byte(0x24); code.U(0); }
        if (ret) code.Get(result);
        EndFunction();
    }
    string Run() {
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
        reservefn = module.AddFn("goose.reserve_frame", {WasmModule::I32}, {WasmModule::I32});
        for (auto sp : ast.fnspecs) if (sp->live) {
            if (sp->sf->isextern) Fail(sp->sf->line, "native extern functions need an explicit Wasm host adapter");
            if (sp->sf->isexport) Fail(sp->sf->line, "exported C interfaces need an explicit Wasm host adapter");
            if (sp->sf->isthread) Fail(sp->sf->line, "workers need the pending isolated-instance adapter");
            if (sp->rets.size() > 1) Fail(sp->sf->line, "multiple results are not implemented");
            vector<uint8_t> args, rets;
            for (auto p : sp->params) args.push_back(Type(p->type));
            for (auto r : sp->rets) rets.push_back(Type(r));
            functions[sp] = module.AddFn(cat(sp->sf->qname, ".", sp->id), args, rets);
        }
        initfn = module.AddFn("goose.init", {}, {});
        startfn = module.AddFn("goose.start", {}, {});
        for (auto g : ast.globals) for (auto v : g->defs) {
            Type(v->type);
            auto offset = module.Data(string(Size(v->type), '\0'));
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
            auto sp = main->specs[0]; code.Call(functions.at(sp));
            for (auto r : sp->rets) { (void)r; code.Byte(0x1a); }
        }
        EndFunction();
        if (f2ifn != UINT32_MAX) EmitFloatToInt();
        module.exports.push_back({"memory", 2, 0});
        module.exports.push_back({"_start", 0, startfn});
        return module.Finish();
    }
};

}  // namespace goose
