// Goose compiler — codegen's builtins (definitions of CodeGen members,
// codegen.h): the builtin functions and array members (§3.3, §5.4), queues
// and threads (§11.2).
#pragma once

namespace goose {

inline string CodeGen::QueueFor(TypeExpr *t) {
    usesthreads = true;
    if (t->kind == TY_NATIVE && t->native->kind == NK_POINTER && !shared_atomic64) {
        shared_atomic64 = true;
        Append(head, "\n#if defined(__TINYC__) || (!defined(__GNUC__) && !defined(__clang__))\n"
                     "#error Native shared pointers require GCC or Clang; this backend is unsupported\n#endif\n"
                     "#if __GCC_ATOMIC_LLONG_LOCK_FREE != 2\n"
                     "#error Native shared pointer reference counts and generation validation require always-lock-free 64-bit atomics\n#endif\n");
    }
    auto m = Mangle(t);
    auto it = queues.find(m);
    if (it != queues.end()) return it->second;
    auto name = Unique(cat("gs_q_", m));
    Append(data, "static gs_queue ", name, " = GS_QUEUE_INIT;\n");
    if (t->kind == TY_NATIVE && t->native->kind == NK_POINTER) pointerqueues.insert(name);
    return queues[m] = name;
}

// The receiver of a member operation, dereferenced, with its stack. The
// arguments run after it and may rebind a reference it is reached through
// (Loc::viaref), so such a receiver is resolved first: a reference is read
// into a temporary, anything else to the addresses it names. A stack whose
// top this body caches is named by a binding nothing rebinds, so it keeps
// that name.
inline CodeGen::Loc CodeGen::RecvLoc(Node *n) {
    auto lv = GenLoc(n);
    if (lv.t->kind == TY_REF) {
        auto orig = lv;
        DerefLoc(orig);
        if (lv.viaref && lv.val && lv.t->ref->lenstorage < 0 && !lv.ispref &&
            (orig.stk.empty() || !CacheableStk(orig.stk))) {
            lv.s = Snapshot(lv.t, lv.s);
            DerefLoc(lv);
        } else {
            lv = orig;
        }
        return lv;
    }
    if (!lv.viaref || (!lv.stk.empty() && CacheableStk(lv.stk))) return lv;
    PinLoc(lv);
    return lv;
}

// The C type a length-field write casts to, per receiver representation.
inline string CodeGen::LenCast(const Loc &lv) {
    auto ak = lv.t->arr->akind;
    if (ak == A_LIMITED) return lv.val ? IntCT(LenStore(lv.t->arr)) : "uint32_t";
    if (ak == A_VAR) return IntCT(LenStore(lv.t->arr));
    return "int64_t";
}

inline vector<string> CodeGen::EmitBuiltin(Call *c, Dst d0) {
    auto an = c->ArgNodes();
    auto ln = c->line;
    if (c->builtin >= B_SHARED_POINTER_ALLOC && c->builtin <= B_SHARED_POINTER_RELEASE) {
        usesthreads = true;
        if (!shared_atomic64) {
            shared_atomic64 = true;
            Append(head, "\n#if defined(__TINYC__) || (!defined(__GNUC__) && !defined(__clang__))\n"
                         "#error Native shared pointers require GCC or Clang; this backend is unsupported\n#endif\n"
                         "#if __GCC_ATOMIC_LLONG_LOCK_FREE != 2\n"
                         "#error Native shared pointer reference counts and generation validation require always-lock-free 64-bit atomics\n#endif\n");
        }
        vector<string> a; for (auto n : an) a.push_back(Snapshot(n->exprtype, GenPure(n)));
        if (c->builtin == B_SHARED_POINTER_ALLOC) {
            auto p = T(), ok = T(); L("uint8_t ", ok, ";");
            if (a.size() == 1) {
                auto o = T(); L("gs_shared_cap ", o, ";");
                L("gs_shared_cap ", p, " = gs_shared_pointer_alloc(&", a[0], ", ", FixedSize(c->qtype), ", &", o, ", &", ok, ", ", LocArgs(ln), ");");
                return {p, o, ok};
            }
            L("gs_shared_cap ", p, " = gs_shared_pointer_alloc_in(", a[0], ", ", a[1], ", &", a[2], ", ", FixedSize(c->qtype), ", &", ok, ", ", LocArgs(ln), ");");
            return {p, ok};
        }
        if (c->builtin == B_SHARED_POINTER_COPY) { auto v = T(); FixedLocal(c->qtype, v);
            L("gs_shared_pointer_copy(", a[0], ", &", v, ", ", FixedSize(c->qtype), ", ", LocArgs(ln), ");"); return {v}; }
        if (c->builtin == B_SHARED_POINTER_STORE) { L("gs_shared_pointer_store(", a[0], ", &", a[1], ", ", FixedSize(c->qtype), ", ", LocArgs(ln), ");"); return {}; }
        if (c->builtin == B_SHARED_POINTER_RETAIN) { auto v = T(); L("gs_shared_cap ", v, " = gs_shared_pointer_retain(", a[0], ", ", LocArgs(ln), ");"); return {v}; }
        L("gs_shared_pointer_release(", a[0], ", ", LocArgs(ln), ");"); return {};
    }
    if (c->builtin >= B_SIMD_SPLAT && c->builtin <= B_SIMD_SHUFFLE) {
        auto t = c->qtype;
        auto lane = t->arr->sub;
        auto lanes = ArrSize(t->arr);
        auto vt = ExplicitVecType(t);
        auto out = T();
        if (c->builtin == B_SIMD_SPLAT) {
            auto x = Snapshot(lane, GenXD(an[0], lane));
            L(CT(t), " ", out, ";");
            string init;
            for (int64_t i = 0; i < lanes; i++) Append(init, i ? ", " : "", x);
            L("#if GS_VEC");
            L("GS_VST(", vt, ", &", out, ", ((", vt, "){", init, "}));");
            L("#else");
            auto i = T();
            L("for (int64_t ", i, " = 0; ", i, " < ", lanes, "; ", i, "++) ",
              out, ".e[", i, "] = ", x, ";");
            L("#endif");
            return {out};
        }
        if (c->builtin == B_SIMD_LOAD || c->builtin == B_SIMD_STORE) {
            auto slice = Snapshot(an[0]->exprtype, GenXD(an[0], an[0]->exprtype));
            auto first = Snapshot(ast.inttypes[IS_I64], GenXD(an[1], ast.inttypes[IS_I64]));
            // Calls evaluate every argument before entering the operation,
            // even when its complete-range check will fail.
            string v;
            if (c->builtin == B_SIMD_STORE) v = Snapshot(t, GenXD(an[2], t));
            L("if (", first, " < 0 || ", slice, ".len < ", lanes, " || ", first,
              " > ", slice, ".len - ", lanes, ") gs_idxfail(", first, " < 0 || ",
              first, " >= ", slice, ".len ? ", first, " : ", slice, ".len, ",
              slice, ".len, ", LocArgs(ln), ");");
            if (c->builtin == B_SIMD_LOAD) {
                L(CT(t), " ", out, ";");
                L("#if GS_VEC");
                L("GS_VST(", vt, ", &", out, ", GS_VLD(", vt, ", ", slice,
                  ".data + ", first, "));");
                L("#else");
                L("GS_MEMCPY(&", out, ", ", slice, ".data + ", first, ", ", FixedSize(t), ");");
                L("#endif");
                return {out};
            }
            L("#if GS_VEC");
            L("GS_VST(", vt, ", ", slice, ".data + ", first, ", GS_VLD(", vt, ", &", v, "));");
            L("#else");
            L("GS_MEMCPY(", slice, ".data + ", first, ", &", v, ", ", FixedSize(t), ");");
            L("#endif");
            return {};
        }
        auto v = Snapshot(t, GenXD(an[0], t));
        vector<string> ix;
        bool constants = true;
        for (size_t k = 1; k < an.size(); k++) {
            auto lit = Is<IntLit>(an[k]);
            // Clang diagnoses an invalid shuffle immediate before the
            // emitted bounds check can run. Preserve the Goose abort.
            constants &= lit && lit->val >= 0 && lit->val < lanes;
        }
        for (size_t k = 1; k < an.size(); k++) {
            auto x = GenXD(an[k], ast.inttypes[IS_I64]);
            ix.push_back(constants ? x : Snapshot(ast.inttypes[IS_I64], x));
        }
        for (auto &i : ix) L("(void)GS_IDX(", i, ", ", lanes, ", ", LocArgs(ln), ");");
        L(CT(t), " ", out, ";");
        if (constants) {
            string args, mask;
            for (auto &i : ix) { Append(args, args.empty() ? "" : ", ", i); Append(mask, mask.empty() ? "" : ", ", i); }
            auto mt = ExplicitMaskVecType(t);
            L("#if GS_VEC && defined(__clang__)");
            L("GS_VST(", vt, ", &", out, ", __builtin_shufflevector(GS_VLD(", vt, ", &", v,
              "), GS_VLD(", vt, ", &", v, "), ", args, "));");
            L("#elif GS_VEC && defined(__GNUC__)");
            L("GS_VST(", vt, ", &", out, ", __builtin_shuffle(GS_VLD(", vt, ", &", v,
              "), (", mt, "){", mask, "}));");
            L("#else");
        }
        for (size_t k = 0; k < ix.size(); k++) L(out, ".e[", k, "] = ", v, ".e[", ix[k], "];");
        if (constants) L("#endif");
        return {out};
    }
    if (c->builtin >= B_UNSAFE_PTR_FROM_HANDLE && c->builtin <= B_UNSAFE_STORE)
        return EmitUnsafeBuiltin(c);
    if (c->builtin >= B_SHARED_ALLOC && c->builtin <= B_MEMORY_COPY) {
        usesthreads = true;
        vector<string> a;
        for (auto n : an) a.push_back(Snapshot(n->exprtype, GenPure(n)));
        auto call = [&](const string &name, const string &params) {
            auto t = T(); L(CT(c->rettypes[0]), " ", t, " = ", name, "(", params,
                           ", ", LocArgs(ln), ");"); return vector<string>{t};
        };
        switch (c->builtin) {
            case B_SHARED_ALLOC: {
                auto out = T(), ok = T(); L("uint8_t ", ok, ";");
                L("gs_shared_cap ", out, " = gs_shared_alloc(", a[0], ", &", ok, ");");
                return {out, ok};
            }
            case B_SHARED_VIEW: return call("gs_shared_view", cat(a[0], ", ", a[1], ", ", a[2]));
            case B_SHARED_CLOSE: return call("gs_shared_close", a[0]);
            case B_SHARED_SIZE: return call("gs_shared_size", a[0]);
            case B_SHARED_BORROW: return a.size() == 1 ? call("gs_shared_borrow", a[0])
                : call("gs_shared_borrow_range", cat(a[0], ", ", a[1], ", ", a[2]));
            case B_SHARED_RELEASE:
                L("gs_shared_release(", a[0], ", ", LocArgs(ln), ");"); return {};
            case B_MEMORY_READ: {
                auto t = T(); L(CT(c->qtype), " ", t, ";");
                L("gs_shared_read(", a[0], ", ", a[1], ", &", t, ", sizeof ", t,
                  ", ", a[2], ", ", LocArgs(ln), ");"); return {t};
            }
            case B_MEMORY_WRITE:
                L("gs_shared_write(", a[0], ", ", a[1], ", &", a[2], ", sizeof ", a[2],
                  ", ", a[3], ", ", LocArgs(ln), ");"); return {};
            case B_MEMORY_COPY:
                L("gs_shared_copy(", a[0], ", ", a[1], ", ", a[2], ", ", a[3], ", ", a[4],
                  ", ", LocArgs(ln), ");"); return {};
            default: assert(false);
        }
    }
    if (c->builtin >= B_UNSAFE_ATOMIC_LOCKFREE && c->builtin <= B_UNSAFE_ATOMIC_CAS) {
        auto bk = c->builtin;
        bool u32 = c->qtype->intstorage == IS_U32;
        int width = u32 ? 4 : 8;
        if (used.insert(u32 ? "raw_atomic32" : "raw_atomic64").second) {
            Append(head, "\n#if defined(__TINYC__) || defined(_MSC_VER) || (!defined(__GNUC__) && !defined(__clang__))\n"
                         "#error Unsafe raw address atomics require GCC or Clang; TinyCC and MSVC unsupported\n#endif\n");
            Append(head, "_Static_assert(__atomic_always_lock_free(", width,
                   ", 0), \"Unsafe raw atomic width is not always lock-free on this target\");\n");
        }
        if (bk == B_UNSAFE_ATOMIC_LOCKFREE) return {cat("__atomic_always_lock_free(", width, ", 0)")};
        vector<string> a;
        size_t nargs = bk == B_UNSAFE_ATOMIC_LOAD ? 1 : bk == B_UNSAFE_ATOMIC_CAS ? 3 : 2;
        for (size_t i = 0; i < nargs; i++) a.push_back(Snapshot(an[i]->exprtype, GenPure(an[i])));
        auto msg = "unsafe atomic address is null, misaligned, or exceeds target width";
        L("if (!", a[0], " || ", a[0], " > UINTPTR_MAX || (", a[0], " & ", width - 1,
          ")) gs_abort_msg((const uint8_t *)", CStr(msg), ", ", strlen(msg), ", ", LocArgs(ln), ");");
        auto ptr = T();
        L(u32 ? "uint32_t *" : "uint64_t *", ptr, " = (", u32 ? "uint32_t" : "uint64_t",
          " *)(uintptr_t)", a[0], ";");
        static const char *orders[] = {"__ATOMIC_RELAXED", "", "__ATOMIC_ACQUIRE", "__ATOMIC_RELEASE", "__ATOMIC_ACQ_REL", "__ATOMIC_SEQ_CST"};
        auto order = orders[c->memory_order];
        if (bk == B_UNSAFE_ATOMIC_STORE) {
            L("__atomic_store_n(", ptr, ", ", a[1], ", ", order, ");"); return {};
        }
        if (bk == B_UNSAFE_ATOMIC_CAS) {
            auto ok = T();
            L("uint8_t ", ok, " = __atomic_compare_exchange_n(", ptr, ", &", a[1], ", ", a[2],
              ", 0, ", order, ", ", orders[c->failure_order], ");");
            return {a[1], ok};
        }
        auto t = T();
        const char *op = bk == B_UNSAFE_ATOMIC_LOAD ? "load" : bk == B_UNSAFE_ATOMIC_EXCHANGE ? "exchange"
                         : bk == B_UNSAFE_ATOMIC_ADD ? "fetch_add" : bk == B_UNSAFE_ATOMIC_SUB ? "fetch_sub"
                         : bk == B_UNSAFE_ATOMIC_AND ? "fetch_and" : bk == B_UNSAFE_ATOMIC_OR ? "fetch_or" : "fetch_xor";
        L(CT(c->qtype), " ", t, " = __atomic_", op,
          bk == B_UNSAFE_ATOMIC_LOAD || bk == B_UNSAFE_ATOMIC_EXCHANGE ? "_n" : "",
          "(", ptr, bk == B_UNSAFE_ATOMIC_LOAD ? "" : cat(", ", a[1]), ", ", order, ");");
        return {t};
    }
    if (c->builtin >= B_SHARED_ATOMIC32 && c->builtin <= B_ATOMIC_CAS) {
        usesthreads = true;
        auto bk = c->builtin;
        bool u32 = bk == B_SHARED_ATOMIC32 || bk == B_SHARED_ATOMIC_ARRAY32 || bk == B_SHARED_ATOMIC_VIEW32 ||
                   (bk >= B_ATOMIC_LOCKFREE && c->qtype->intstorage == IS_U32);
        int width = u32 ? 4 : 8;
        bool &usedwidth = u32 ? shared_atomic32 : shared_atomic64;
        if (!usedwidth) {
            usedwidth = true;
            Append(head, "\n#if defined(__TINYC__) || (!defined(__GNUC__) && !defined(__clang__))\n"
                         "#error Native shared atomics require GCC or Clang; this backend is unsupported\n#endif\n");
            Append(head, "#if ", u32 ? "__GCC_ATOMIC_INT_LOCK_FREE" : "__GCC_ATOMIC_LLONG_LOCK_FREE",
                   " != 2\n#error Native shared atomic width is not always lock-free on this target\n#endif\n");
            Append(head, "#if __GCC_ATOMIC_LLONG_LOCK_FREE != 2\n"
                         "#error Native shared atomic generation validation requires always-lock-free 64-bit atomics\n#endif\n");
        }
        vector<string> a;
        size_t nargs = bk == B_ATOMIC_LOAD || bk == B_ATOMIC_LOCKFREE ? 1 : bk == B_ATOMIC_CAS ? 3
                      : bk >= B_ATOMIC_STORE ? 2 : an.size();
        for (size_t i = 0; i < nargs; i++) a.push_back(Snapshot(an[i]->exprtype, GenPure(an[i])));
        if (bk <= B_SHARED_ATOMIC_ARRAY64) {
            bool array = bk >= B_SHARED_ATOMIC_ARRAY32;
            auto region = T();
            L("gs_shared_cap ", region, " = gs_shared_atomic_region(", a[0], ", ", a[1], ", ",
              array ? a[2] : "1", ", ", width, ", ", a[array ? 3 : 2], ", ", LocArgs(ln), ");");
            if (array) return {region};
            auto t = T(); L("gs_shared_atomic_cap ", t, " = {", region, ".slot, ", region, ".generation, 0};");
            return {t};
        }
        bool derive = bk == B_SHARED_ATOMIC_VIEW32 || bk == B_SHARED_ATOMIC_VIEW64;
        auto index = derive ? a[1] : cat(a[0], ".index");
        auto rec = T(); L("gs_shared_record *", rec, " = NULL;");
        auto msg = "invalid, closed, misaligned, or out-of-bounds shared atomic capability";
        L("if (!", a[0], ".generation || ", a[0], ".slot >= GS_SHARED_MAX || ",
          "!gs_shared_slabs[", a[0], ".slot / GS_SHARED_SLAB_SIZE] || ",
          "!(", rec, " = &gs_shared_slabs[", a[0], ".slot / GS_SHARED_SLAB_SIZE][", a[0], ".slot % GS_SHARED_SLAB_SIZE]) || ",
          "__atomic_load_n(&", rec, "->generation, __ATOMIC_ACQUIRE) != ", a[0], ".generation || ",
          rec, "->kind != ", u32 ? 4 : 5, " || ", index, " >= ", rec, "->size / ", width,
          " || ((uintptr_t)", rec, "->data & ", width - 1, ")) ",
          "gs_abort_msg((const uint8_t *)\"", msg, "\", ", strlen(msg), ", ", LocArgs(ln), ");");
        if (derive) {
            auto t = T(); L("gs_shared_atomic_cap ", t, " = {", a[0], ".slot, ", a[0], ".generation, ", index, "};"); return {t};
        }
        if (bk == B_ATOMIC_LOCKFREE) return {cat("__atomic_always_lock_free(", width, ", 0)")};
        auto ptr = T(); L(u32 ? "uint32_t *" : "uint64_t *", ptr, " = (", u32 ? "uint32_t" : "uint64_t", " *)(", rec, "->data + ", index, " * ", width, ");");
        static const char *orders[] = {"__ATOMIC_RELAXED", "", "__ATOMIC_ACQUIRE", "__ATOMIC_RELEASE", "__ATOMIC_ACQ_REL", "__ATOMIC_SEQ_CST"};
        auto order = orders[c->memory_order];
        if (bk == B_ATOMIC_STORE) { L("__atomic_store_n(", ptr, ", ", a[1], ", ", order, ");"); return {}; }
        if (bk == B_ATOMIC_CAS) {
            auto ok = T(); L("uint8_t ", ok, " = __atomic_compare_exchange_n(", ptr, ", &", a[1], ", ", a[2],
                            ", 0, ", order, ", ", orders[c->failure_order], ");"); return {a[1], ok};
        }
        const char *op = bk == B_ATOMIC_LOAD ? "load" : bk == B_ATOMIC_EXCHANGE ? "exchange"
                         : bk == B_ATOMIC_ADD ? "fetch_add" : bk == B_ATOMIC_SUB ? "fetch_sub"
                         : bk == B_ATOMIC_AND ? "fetch_and" : bk == B_ATOMIC_OR ? "fetch_or" : "fetch_xor";
        auto t = T(); L(CT(c->qtype), " ", t, " = __atomic_", op,
                       bk == B_ATOMIC_LOAD || bk == B_ATOMIC_EXCHANGE ? "_n" : "", "(", ptr,
                       bk == B_ATOMIC_LOAD ? "" : cat(", ", a[1]), ", ", order, ");"); return {t};
    }
    if (c->builtin >= B_SHARED_MAP && c->builtin <= B_MEMORY_WRITE_BYTES) {
        usesthreads = true;
        vector<string> a;
        for (size_t i = 0; i < (c->builtin == B_SHARED_ADVICE ? 3 : an.size()); i++)
            a.push_back(Snapshot(an[i]->exprtype, GenPure(an[i])));
        if (c->builtin == B_SHARED_MAP) {
            auto t = T(), ok = T(); L("uint8_t ", ok, ";");
            L("gs_shared_cap ", t, " = gs_shared_map_readonly(", a[0], ".data, ", a[0], ".len, ", a[1], ", &", ok, ");");
            return {t, ok};
        }
        if (c->builtin == B_SHARED_ADVICE) {
            auto t = T(); L("int ", t, " = gs_shared_page_advice(", a[0], ", ", a[1], ", ", a[2], ", ",
                            c->memory_order, ", ", LocArgs(ln), ");");
            return {cat("(", t, " != 0)"), cat("(", t, " == 2)")};
        }
        L("gs_shared_bytes(", a[0], ", ", a[1], ", (void *)", a[2], ".data, ", a[2], ".len, ",
          c->builtin == B_MEMORY_WRITE_BYTES ? 1 : 0, ", ", LocArgs(ln), ");"); return {};
    }
    switch ((BuiltinKind)c->builtin) {
        case B_PRINT: {
            // The whole line, newline included, is rendered before any of
            // it is written, so an argument that prints on its own (a call)
            // cannot interleave with it, and it goes out as one write (§3.7).
            auto b = TempBuilder();
            for (auto a : an) EmitFormatInto(b, a, ln, c);
            RenderLit(b, "\n");
            L("gs_out_bytes(", b.hdr, ".base, ", b.hdr, ".len);");
            return {};
        }
        case B_STR: return EmitStr(c, an, d0, ln);
        case B_FORMAT: {
            auto lv = RecvLoc(an[0]);
            for (size_t i = 1; i < an.size(); i++) EmitFormatInto(lv, an[i], ln, c);
            return {};
        }
        case B_ASSERT: {
            if (BranchChain(an[0])) {
                auto ok = Lbl();
                GenBranch(an[0], true, ok);
                L("gs_abort(GS_E_ASSERT, ", LocArgs(ln), ");");
                L(ok, ":;");
                return {};
            }
            auto x = GenTruth(an[0]);
            L("if (!(", x, ")) gs_abort(GS_E_ASSERT, ", LocArgs(ln), ");");
            return {};
        }
        case B_ABORT: {
            auto x = GenPure(an[0]);
            L("gs_abort_msg(", x, ".data, ", x, ".len, ", LocArgs(ln), ");");
            return {};
        }
        case B_EXIT:
            L("gs_exit(", GenX(an[0]), ");");
            return {};
        case B_COPY: {
            if (c->exprtype->kind != TY_SLICE)
                return { LoadLoc(GenLoc(an[0]), c->exprtype, ln) };
            // A slice destination views the copy's temporary, not its source.
            auto slice = c->exprtype;
            c->exprtype = c->rettypes[0];
            auto lv = GenLoc(c);
            c->exprtype = slice;
            return { LoadLoc(lv, slice, ln) };
        }
        case B_MOVE_FROM: {
            auto dst = ArrayView(RecvLoc(an[0]));
            auto base = T(), count = T();
            L("uint8_t *", base, " = (uint8_t *)(", dst.elems, ");");
            L("int64_t ", count, " = ", dst.len, ";");
            auto src = GenPure(an[1]);
            L("if (", count, " != ", src,
              ".len) gs_abort_msg((const uint8_t *)\"move_from lengths differ\", "
              "sizeof(\"move_from lengths differ\") - 1, ", LocArgs(ln), ");");
            auto size = FixedSize(dst.elem);
            if (size) L("if (", count, ") memmove(", base, ", ", src, ".data, (size_t)", count, " * ", size, ");");
            return {};
        }
        case B_TO_BYTES: return EmitToBytes(an, d0, ln);
        case B_BYTES_OF: return EmitBytesOf(c, an, ln);
        case B_READ_RECORD_LE: return EmitRecordRead(c, an);
        case B_FROM_BYTES: return EmitFromBytes(c, an, d0, ln);
        case B_DEFAULT: {
            auto t = c->rettypes[0];
            auto tv = T();
            FixedLocal(t, tv);
            if (!HasFieldDefaults(t)) EmitDefaultInto(tv, t);
            else if (t->kind == TY_ARRAY) {
                auto i = T();
                L("for (int64_t ", i, " = 0; ", i, " < ", ArrSize(t->arr), "; ", i, "++) {");
                ind++;
                PushSc(SC_PLAIN);
                GenAny(c->defaultinit, Dst { DK_LVALUE, cat(tv, ".e[", i, "]"), t->arr->sub });
                PopSc();
                ind--;
                L("}");
            } else GenAny(c->defaultinit, Dst { DK_LVALUE, tv, t });
            return { tv };
        }
        case B_HARDWARE_THREADS: return { "gs_hardware_threads()" };
        case B_EMBED_SHADER:
        case B_EMBED_FILE: {
            auto &blob = *c->shaderblob;
            auto t = T();
            L(CT(c->rettypes[0]), " ", t, " = { ", BlobRaw(blob), ", ", blob.size(), " };");
            return { t };
        }
        case B_THREAD_WAIT: {
            usesthreads = true;
            // Emitted here, not returned as text: a discarded result would
            // drop the wait.
            auto t = T();
            if (an.size() == 1) {
                auto id = GenX(an[0]);
                L("uint8_t ", t, " = gs_thread_wait(", id, ", NULL, NULL, ", LocArgs(ln), ");");
                return { t };
            }
            // thread_wait(id, msg): the abort's message, which this wait takes
            // if no wait has, appended to msg.
            auto id = GenX(an[0]);
            auto m = T(), n = T();
            L("uint8_t *", m, ";");
            L("int64_t ", n, ";");
            L("uint8_t ", t, " = gs_thread_wait(", id, ", &", m, ", &", n, ", ", LocArgs(ln),
              ");");
            L("if (", m, ") {");
            ind++;
            AppendBytes(RecvLoc(an[1]), m, n, ln);
            L("gs_free_msg(", m, ");");
            ind--;
            L("}");
            return { t };
        }
        case B_THREAD_JOIN: {
            usesthreads = true;
            auto rt = c->rettypes[0]; auto h = GenX(an[0]);
            auto n = T(), p = T(), msg = T(), mlen = T();
            L("int64_t ", n, ", ", mlen, " = 0; uint8_t *", msg, " = NULL;");
            L("uint8_t *", p, " = gs_thread_join(", h, ", &", n, ", ",
              an.size() == 2 ? cat("&", msg, ", &", mlen) : string("NULL, NULL"),
              ", ", LocArgs(ln), ");");
            if (an.size() == 2) {
                L("if (", msg, ") {"); ind++; AppendBytes(RecvLoc(an[1]), msg, mlen, ln);
                L("gs_free_msg(", msg, ");"); ind--; L("}");
            }
            auto ok = T(); L("uint8_t ", ok, " = ", p, " != NULL;");
            if (IsResz(rt)) {
                EmitCoreTypes();
                string stk = d0.k == DK_STACK && !d0.lenlv.empty() ? d0.s : "";
                string lenlv = d0.k == DK_STACK ? d0.lenlv : "";
                string hv;
                if (stk.empty()) { hv = RzTemp(rt, stk); lenlv = RzLenLv(rt, hv); }
                auto fo = IsFrameObj(rt);
                auto cnt = fo ? cat(FoTailHdr(rt, lenlv), ".len") : lenlv;
                auto image = cat(p, " + 8");
                auto bytes = cat("(", n, " - 8)");
                if (fo) {
                    L("GS_MEMZERO(&", lenlv, ", sizeof(", lenlv, "));");
                    L(FoTailHdr(rt, lenlv), ".base = ", Top(stk), ";");
                } else L(lenlv, " = 0;");
                L("if (", p, ") {"); ind++;
                if (fo) {
                    auto pre = FoPrefixSize(rt);
                    L("GS_MEMCPY(&", lenlv, ", ", image, ", ", pre, ");");
                    image = cat(image, " + ", pre); bytes = cat("(", n, " - 8 - ", pre, ")");
                }
                L("GS_MEMCPY(&", cnt, ", ", p, ", 8);");
                L("GS_MEMCPY(", Top(stk), ", ", image, ", (size_t)", bytes, ");");
                Bump(stk, bytes); L("free(", p, ");"); ind--; L("}");
                return { hv, ok };
            }
            if (IsBytesT(rt)) {
                string stk = d0.k == DK_STACK ? d0.s : ""; string base = T();
                if (stk.empty()) { stk = AllocStk(false); L("uint8_t *", base, " = ", Top(stk), ";"); SaveBase(false, stk, base); }
                else L("uint8_t *", base, " = ", Top(stk), ";");
                L("if (", p, ") { GS_MEMCPY(", Top(stk), ", ", p, ", (size_t)", n, ");");
                ind++; Bump(stk, n); L("free(", p, ");"); ind--; L("} else {"); ind++;
                L("GS_MEMZERO(", Top(stk), ", ", MinBytes(rt, true), ");");
                Bump(stk, cat(MinBytes(rt, true))); ind--; L("}");
                return { base, ok };
            }
            auto v = T(); FixedLocal(rt, v);
            L("GS_MEMZERO(&", v, ", sizeof(", v, "));");
            L("if (", p, ") { GS_MEMCPY(&", v, ", ", p, ", ", FixedSize(rt), "); free(", p, "); }");
            return { v, ok };
        }
        case B_THREAD_SPAWN: case B_THREAD_SPAWN_CONTAINED:
        case B_THREAD_SPAWN_JOIN: case B_THREAD_SPAWN_CONTAINED_JOIN:
            return EmitThreadSpawn(c, an);
        case B_THREAD_CANCELLED:
            usesthreads = true;
            return { "gs_thread_cancelled()" };
        case B_THREAD_CANCEL: {
            auto h = GenX(an[0]);
            auto v = T();
            L("uint8_t ", v, " = gs_thread_cancel(", h, ", ", LocArgs(ln), ");");
            return { v };
        }
        case B_CHANNEL: {
            usesthreads = true;
            auto limit = an.empty() ? string("INT64_MAX") : GenX(an[0]);
            auto v = T();
            L("gs_handle ", v, " = gs_channel_create(", limit, ", ", LocArgs(ln), ");");
            return { v };
        }
        case B_CHANNEL_CLOSE: {
            auto h = GenX(an[0]);
            auto v = T();
            L("uint8_t ", v, " = gs_channel_close(", h, ", ", LocArgs(ln), ");");
            return { v };
        }
        case B_CHANNEL_WAIT_ANY: {
            auto hs = T();
            L("gs_handle ", hs, "[", an.size(), "];");
            for (size_t i = 0; i < an.size(); i++) L(hs, "[", i, "] = ", GenX(an[i]), ";");
            auto v = T();
            L("int64_t ", v, " = gs_channel_wait_any(", hs, ", ", an.size(), ", ", LocArgs(ln), ");");
            return { v };
        }
        case B_CHANNEL_SEND: case B_CHANNEL_TRY_SEND: {
            auto t = c->qtype; auto h = GenPure(an[0]); auto ok = T();
            auto wait = c->builtin == B_CHANNEL_SEND ? "1" : "0";
            if (IsResz(t)) {
                // Construct the accepted payload conversion into its image;
                // a stored argument may still have a fixed/limited layout.
                string stk; auto base = BytesTemp(stk);
                auto cnt = T(); L("int64_t ", cnt, " = 0;");
                Bump(stk, "8");
                if (IsFrameObj(t)) {
                    auto pre = FoPrefixSize(t), pp = T(), header = T();
                    L("uint8_t *", pp, " = ", Top(stk), ";");
                    Bump(stk, pre);
                    L(CT(t), " ", header, ";");
                    GenConstruct(an[1], stk, t, header);
                    L(cnt, " = ", FoTailHdr(t, header), ".len;");
                    L("GS_MEMCPY(", pp, ", &", header, ", ", pre, ");");
                } else GenConstruct(an[1], stk, t, cnt);
                L("GS_MEMCPY(", base, ", &", cnt, ", 8);");
                L("uint8_t ", ok, " = gs_channel_send(", h, ", ", base, ", ", Top(stk),
                  " - ", base, ", ", wait, ", ", LocArgs(ln), ");");
            } else if (IsBytesT(t)) {
                string stk; auto p = BytesTemp(stk);
                GenConstruct(an[1], stk, t);
                L("uint8_t ", ok, " = gs_channel_send(", h, ", ", p, ", ", Top(stk), " - ", p,
                  ", ", wait, ", ", LocArgs(ln), ");");
            } else {
                auto tv = T(); FixedLocal(t, tv);
                GenAny(an[1], Dst { DK_LVALUE, tv, t });
                L("uint8_t ", ok, " = gs_channel_send(", h, ", &", tv, ", ", FixedSize(t),
                  ", ", wait, ", ", LocArgs(ln), ");");
            }
            return { ok };
        }
        case B_CHANNEL_RECEIVE: case B_CHANNEL_TRY_RECEIVE: {
            auto t = c->rettypes[0]; auto h = GenX(an[0]); auto nn = T();
            L("gs_qnode *", nn, " = gs_channel_receive(", h, ", ",
              c->builtin == B_CHANNEL_RECEIVE ? "1" : "0", ", ", LocArgs(ln), ");");
            auto got = T(); L("uint8_t ", got, " = ", nn, " != NULL;");
            if (IsResz(t)) {
                EmitCoreTypes(); string stk = d0.k == DK_STACK && !d0.lenlv.empty() ? d0.s : "";
                string lenlv = d0.k == DK_STACK ? d0.lenlv : ""; string hv;
                if (stk.empty()) { hv = RzTemp(t, stk); lenlv = RzLenLv(t, hv); }
                auto fo = IsFrameObj(t); auto cnt = fo ? cat(FoTailHdr(t, lenlv), ".len") : lenlv;
                auto image = cat("(uint8_t *)(", nn, " + 1) + 8");
                auto bytes = cat("(", nn, "->size - 8)");
                if (fo) { L("GS_MEMZERO(&", lenlv, ", sizeof(", lenlv, "));"); L(FoTailHdr(t, lenlv), ".base = ", Top(stk), ";"); }
                else L(lenlv, " = 0;");
                L("if (", nn, ") {"); ind++;
                if (fo) { auto pre = FoPrefixSize(t); L("GS_MEMCPY(&", lenlv, ", ", image, ", ", pre, ");"); image = cat(image, " + ", pre); bytes = cat("(", nn, "->size - 8 - ", pre, ")"); }
                L("GS_MEMCPY(&", cnt, ", ", nn, " + 1, 8);");
                L("GS_MEMCPY(", Top(stk), ", ", image, ", (size_t)", bytes, ");");
                Bump(stk, bytes); L("free(", nn, ");"); ind--; L("}");
                return { hv, got };
            }
            if (IsBytesT(t)) {
                string stk = d0.k == DK_STACK ? d0.s : ""; string base = T();
                if (stk.empty()) { stk = AllocStk(false); L("uint8_t *", base, " = ", Top(stk), ";"); SaveBase(false, stk, base); }
                else L("uint8_t *", base, " = ", Top(stk), ";");
                L("if (", nn, ") {"); ind++; L("GS_MEMCPY(", Top(stk), ", ", nn, " + 1, (size_t)", nn, "->size);");
                Bump(stk, cat(nn, "->size")); L("free(", nn, ");"); ind--; L("} else {"); ind++;
                L("GS_MEMZERO(", Top(stk), ", ", MinBytes(t, true), ");"); Bump(stk, cat(MinBytes(t, true))); ind--; L("}");
                return { base, got };
            }
            auto v = T(); FixedLocal(t, v); L("GS_MEMZERO(&", v, ", sizeof(", v, "));");
            L("if (", nn, ") { GS_MEMCPY(&", v, ", ", nn, " + 1, ", FixedSize(t), "); free(", nn, "); }");
            return { v, got };
        }
        case B_QPUT: {
            auto t = an[0]->exprtype;
            auto q = QueueFor(t);
            // Emitted here, not returned as text: a discarded result would
            // drop the put.
            auto ok = T();
            if (t->kind == TY_NATIVE && t->native->kind == NK_POINTER) {
                auto src = Snapshot(t, GenPure(an[0])), queued = T();
                L("gs_shared_cap ", queued, " = gs_shared_pointer_retain(", src, ", ", LocArgs(ln), ");");
                L("gs_shared_pointer_queue(", queued, ", ", LocArgs(ln), ");");
                L("uint8_t ", ok, " = gs_qput(&", q, ", &", queued, ", sizeof ", queued, ");");
                L("if (", ok, ") gs_shared_pointer_release(", src, ", ", LocArgs(ln), ");");
                L("else { gs_shared_pointer_adopt(", queued, ", ", LocArgs(ln), "); gs_shared_pointer_release(", queued, ", ", LocArgs(ln), "); }");
            } else if (IsResz(t)) {
                auto src = GenLoc(an[0]);
                if (src.t->kind == TY_REF) DerefLoc(src);
                string stk;
                auto base = BytesTemp(stk);
                EmitRzImage(src, t, stk, ln);
                L("uint8_t ", ok, " = gs_qput(&", q, ", ", base, ", ", Top(stk), " - ", base, ");");
            } else if (IsBytesT(t)) {
                auto p = GenPtr(an[0]);
                L("uint8_t ", ok, " = gs_qput(&", q, ", ", p, ", ", SizeX(t, p), ");");
            } else {
                auto tv = T();
                FixedLocal(t, tv, GenX(an[0]));
                L("uint8_t ", ok, " = gs_qput(&", q, ", &", tv, ", ", FixedSize(t), ");");
            }
            return { ok };
        }
        case B_QLIMIT: {
            auto q = QueueFor(c->qtype);
            auto n = GenX(an[0]);
            L("gs_qlimit(&", q, ", ", n, ", ", LocArgs(ln), ");");
            return {};
        }
        case B_QGET: case B_QPOLL: {
            auto t = c->rettypes[0];
            auto q = QueueFor(t);
            auto nn = T();
            // qpoll<T>() and qget<T>(ms) say whether a value came.
            auto poll = c->rettypes.size() > 1;
            if (c->builtin == B_QPOLL) L("gs_qnode *", nn, " = gs_qpoll(&", q, ");");
            else if (poll) L("gs_qnode *", nn, " = gs_qwait(&", q, ", ", GenX(an[0]), ");");
            else L("gs_qnode *", nn, " = gs_qget(&", q, ");");
            string got;
            if (poll) {
                got = T();
                L("uint8_t ", got, " = ", nn, " != NULL;");
            }
            if (IsResz(t)) {
                // The image is [int64 count][fixed fields][tail elements]
                // (see qput). The elements go to the destination's top;
                // the count, and a frame object's fixed fields, to the
                // receiving header or frame object (a temporary without
                // a receiver).
                EmitCoreTypes();
                string stk = d0.k == DK_STACK && !d0.lenlv.empty() ? d0.s : "";
                string lenlv = d0.k == DK_STACK ? d0.lenlv : "";
                string hv;
                if (stk.empty()) {
                    hv = RzTemp(t, stk);
                    lenlv = RzLenLv(t, hv);
                }
                auto fo = IsFrameObj(t);
                auto cnt = fo ? cat(FoTailHdr(t, lenlv), ".len") : lenlv;
                auto image = cat("(uint8_t *)(", nn, " + 1) + 8");
                auto n = cat("(", nn, "->size - 8)");
                if (fo) {
                    // The zero value until the image is read (a missed poll
                    // leaves it), with the tail header at the top, where
                    // the elements land.
                    L("GS_MEMZERO(&", lenlv, ", sizeof(", lenlv, "));");
                    L(FoTailHdr(t, lenlv), ".base = ", Top(stk), ";");
                } else if (poll) {
                    L(lenlv, " = 0;");
                }
                L(poll ? cat("if (", nn, ") {") : string("{"));
                ind++;
                if (fo) {
                    auto pre = FoPrefixSize(t);
                    L("GS_MEMCPY(&", lenlv, ", ", image, ", ", pre, ");");
                    image = cat(image, " + ", pre);
                    n = cat("(", nn, "->size - 8 - ", pre, ")");
                }
                L(cnt, " = *(gs_i64 *)(", nn, " + 1);");
                L("GS_MEMCPY(", Top(stk), ", ", image, ", (size_t)", n, ");");
                Bump(stk, n);
                L("free(", nn, ");");
                ind--;
                L("}");
                return poll ? vector<string> { hv, got } : vector<string> { hv };
            }
            if (IsBytesT(t)) {
                string stk = d0.k == DK_STACK ? d0.s : "";
                string base = T();
                if (stk.empty()) {
                    stk = AllocStk(false);
                    L("uint8_t *", base, " = ", Top(stk), ";");
                    SaveBase(false, stk, base);
                } else {
                    L("uint8_t *", base, " = ", Top(stk), ";");
                }
                if (poll) L("if (", nn, ") {");
                else L("{");
                ind++;
                L("GS_MEMCPY(", Top(stk), ", ", nn, " + 1, (size_t)", nn, "->size);");
                Bump(stk, cat(nn, "->size"));
                L("free(", nn, ");");
                ind--;
                if (poll) {
                    // A missed poll still yields a valid (zero) value.
                    L("} else {");
                    ind++;
                    L("GS_MEMZERO(", Top(stk), ", ", MinBytes(t, true), ");");
                    Bump(stk, cat(MinBytes(t, true)));
                    ind--;
                }
                L("}");
                return poll ? vector<string> { base, got } : vector<string> { base };
            }
            auto tv = T();
            FixedLocal(t, tv);
            if (!FixedSize(t)) {
                // A value of no bytes (§3.4): the node holds none to fill the
                // object C gives it.
                L("GS_MEMZERO(&", tv, ", sizeof(", tv, "));");
                L("free(", nn, ");");
            } else if (poll) {
                L("GS_MEMZERO(&", tv, ", sizeof(", tv, "));");
                L("if (", nn, ") { GS_MEMCPY(&", tv, ", ", nn, " + 1, sizeof(", tv,
                  ")); free(", nn, "); }");
            } else {
                L("GS_MEMCPY(&", tv, ", ", nn, " + 1, sizeof(", tv, "));");
                L("free(", nn, ");");
            }
            if (t->kind == TY_NATIVE && t->native->kind == NK_POINTER)
                L("if (", nn, ") gs_shared_pointer_adopt(", tv, ", ", LocArgs(ln), ");");
            return poll ? vector<string> { tv, got } : vector<string> { tv };
        }
        case B_PUSH: return EmitPush(an, ln);
        case B_APPEND: EmitAppend(an, ln); return {};
        case B_INDEX_OF: {
            // The checker proved the reference is an element of this very
            // array (§3.3), so the distance is a whole number of elements
            // inside the length: an exact divide, nothing to check.
            auto lv = RecvLoc(an[0]);
            auto v = ArrayView(lv);
            auto rx = GenX(an[1]);
            return { cat("(((uint8_t *)(", rx, ") - (uint8_t *)(", v.elems, ")) / ",
                         FixedSize(v.elem), ")") };
        }
        case B_CHECK_LENGTH: {
            auto lv = RecvLoc(an[0]);
            return { SliceLen(an[1], ArrayView(lv).elem, ln, "GS_E_ARRAYLEN",
                              an.size() > 2 ? an[2] : nullptr) };
        }
        case B_RANGE_INDEX: {
            auto lv = RecvLoc(an[0]);
            auto v = ArrayView(lv);
            auto sv = GenPure(an[1]);
            auto esz = FixedSize(v.elem);
            auto fail = FailCall("GS_E_ARRAYSLICE", an.size() > 2 ? an[2] : nullptr, ln);
            auto i = T();
            L("int64_t ", i, " = 0;");
            if (!esz) {
                L("if ((uint64_t)", sv, ".len > (uint64_t)(", v.len, ")) ", fail, ";");
            } else if (!c->poolcheck) {
                L("if (", sv, ".len) ", i, " = ((uint8_t *)", sv,
                  ".data - (uint8_t *)(", v.elems, ")) / ", esz, ";");
            } else {
                L("if (", sv, ".len) {");
                ind++;
                auto off = T();
                L("uint64_t ", off, " = (uint64_t)((uintptr_t)", sv,
                  ".data - (uintptr_t)(", v.elems, "));");
                L("if (", off, " % ", esz, " || ", off, " / ", esz,
                  " >= (uint64_t)(", v.len, ") || (uint64_t)", sv,
                  ".len > (uint64_t)(", v.len, ") - ", off, " / ", esz, ") ", fail, ";");
                L(i, " = (int64_t)(", off, " / ", esz, ");");
                ind--;
                L("}");
            }
            return { i };
        }
        case B_POP: {
            auto lv = RecvLoc(an[0]);
            auto v = ArrayView(lv);
            auto elem = v.elem;
            auto esz = FixedSize(elem);
            auto ak = lv.t->arr->akind;
            string at;
            if (ak == A_GROWSHRINK || ak == A_GROW) {
                NoteLen(lv.stk, v.lenlv, lv.lenroot);
                // On empty, the stack top would drop below the elements.
                if (!c->nobc)
                    L("if (", v.len, " <= 0) gs_abort(GS_E_POP, ", LocArgs(ln), ");");
                L(v.lenlv, "--;");
                // The array tops its stack: the element region ends at top.
                L(TopW(lv.stk), " -= ", esz, ";");
                at = Top(lv.stk);
            } else {
                auto nl = T();
                L("int64_t ", nl, " = ", v.len, " - 1;");
                // On empty, the stored length would wrap.
                if (!c->nobc) L("if (", nl, " < 0) gs_abort(GS_E_POP, ", LocArgs(ln), ");");
                L(v.lenlv, " = (", LenCast(lv), ")", nl, ";");
                at = cat("(", ElemAddr(v, nl), ")");
            }
            // The element leaves as a read of the slot it leaves, whose
            // bytes nothing writes over until the array grows again: a
            // destination stores it at once, and an operand followed by
            // statements is read into a temporary first (GenOperandVal). A
            // relative-reference element is the plain reference it loads as
            // (§3.9), its offset measured from that slot.
            if (IsRelRef(elem))
                return { LoadLoc(BytesLoc(at, elem, lv), c->rettypes[0], ln) };
            return { cat("(*(", CT(elem), " *)", at, ")") };
        }
        case B_POP_N: {
            auto lv = RecvLoc(an[0]);
            auto v = ArrayView(lv);
            auto ak = lv.t->arr->akind;
            if (ak != A_LIMITED) NoteLen(lv.stk, v.lenlv, lv.lenroot);
            auto nn = GenPure(an[1]);
            // The length is read after the count, which may have changed it.
            auto ol = T();
            L("int64_t ", ol, " = ", v.len, ";");
            // One unsigned compare rejects both a count past the length and
            // a negative one, which wraps to above any length.
            L("if ((uint64_t)(", nn, ") > (uint64_t)", ol, ") gs_abort(GS_E_POPN, ",
              LocArgs(ln), ");");
            L(v.lenlv, " = (", LenCast(lv), ")(", ol, " - (int64_t)(", nn, "));");
            if (ak == A_GROWSHRINK || ak == A_GROW)
                L(TopW(lv.stk), " -= (int64_t)(", nn, ") * ", FixedSize(v.elem), ";");
            return {};
        }
        case B_RESIZE: {
            auto lv = RecvLoc(an[0]);
            auto v = ArrayView(lv);
            auto elem = v.elem;
            auto esz = FixedSize(elem);
            auto ak = lv.t->arr->akind;
            auto relref = IsRelRef(elem);
            if (ak != A_LIMITED) NoteLen(lv.stk, v.lenlv, lv.lenroot);
            auto nn = GenPure(an[1]);
            string fv;
            if (an.size() > 2) {
                if (relref) {
                    fv = T();
                    L("uint8_t *", fv, " = (uint8_t *)(", GenX(an[2]), ");");
                } else fv = GenPure(an[2]);
            }
            auto ol = T();
            L("int64_t ", ol, " = ", v.len, ";");
            // A negative target length shrinks past empty: the same
            // corruption as a pop on an empty array. An unsigned `n` above
            // INT64_MAX casts negative and is rejected here as well.
            L("if ((int64_t)(", nn, ") < 0) gs_abort(GS_E_RESIZENEG, ", LocArgs(ln),
              ");");
            L("if (", nn, " < ", ol, ") {");
            ind++;
            L(v.lenlv, " = (", LenCast(lv), ")", nn, ";");
            if (ak == A_GROWSHRINK || ak == A_GROW)
                L(TopW(lv.stk), " = (uint8_t *)(", v.elems, ") + ", nn, " * ", esz, ";");
            ind--;
            L("} else if (", nn, " > ", ol, ") {");
            ind++;
            if (fv.empty()) {
                L("gs_abort(GS_E_RESIZEFILL, ", LocArgs(ln), ");");
            } else {
                if (ak == A_LIMITED)
                    L("if (", nn, " > ", LimitedCap(lv), ") gs_abort(GS_E_CAPACITY, ",
                      LocArgs(ln), ");");
                // The new slots of a resizable are filled through a cursor of
                // their own, so no element store can be taken to change the
                // stack's top (a byte store may alias it in C), and the top
                // is written once, after the fill.
                string cur;
                if (ak != A_LIMITED && !(relref && elem->ref->lenstorage == IS_VARINT)) {
                    cur = T();
                    L("uint8_t *", cur, " = ", Top(lv.stk), ";");
                }
                int fillbyte = 0;
                if (!cur.empty() && !relref && UniformFillByte(an[2], elem, fillbyte)) {
                    auto bytes = cat("(", nn, " - ", ol, ") * ", esz);
                    L("memset(", cur, ", ", fillbyte, ", (size_t)(", bytes, "));");
                    L(cur, " += ", bytes, ";");
                } else {
                    auto iv = T();
                    L("for (int64_t ", iv, " = ", ol, "; ", iv, " < ", nn, "; ", iv, "++) {");
                    ind++;
                    if (relref) {
                        if (ak == A_LIMITED) {
                            EmitRelStoreAt(cat("(uint8_t *)(", ElemAddr(v, iv), ")"), elem, fv, ln,
                                           true);
                        } else if (cur.empty()) {
                            EmitRelStore(lv.stk, elem, fv, ln);
                        } else {
                            EmitRelStoreAt(cur, elem, fv, ln, true);
                            L(cur, " += ", esz, ";");
                        }
                    } else if (ak == A_LIMITED) {
                        if (v.typedelems) L(v.elems, "[", iv, "] = ", fv, ";");
                        else L("*(", CT(elem), " *)(", ElemAddr(v, iv), ") = ", fv, ";");
                    } else {
                        L("*(", CT(elem), " *)", cur, " = ", fv, ";");
                        L(cur, " += ", esz, ";");
                    }
                    ind--;
                    L("}");
                }
                if (!cur.empty()) L(TopW(lv.stk), " = ", cur, ";");
                L(v.lenlv, " = (", LenCast(lv), ")", nn, ";");
            }
            ind--;
            L("}");
            return {};
        }
        case B_CLEAR: {
            auto lv = RecvLoc(an[0]);
            auto v = ArrayView(lv);
            // A resizable is the topmost value on its stack for its whole
            // life (§1.3), so both flavors hand the element region back by
            // dropping the top to the base; a limited array's capacity is
            // reserved and only its length moves.
            auto ak = lv.t->arr->akind;
            if (ak == A_GROWSHRINK || ak == A_GROW) {
                NoteLen(lv.stk, v.lenlv, lv.lenroot);
                L(TopW(lv.stk), " = (uint8_t *)(", v.elems, ");");
            }
            L(v.lenlv, " = 0;");
            return {};
        }
        case B_ALLOC_INDEX: case B_ALLOC_REF: return EmitAlloc(c, an, ln);
        case B_ALLOC_SLICE: case B_REALLOC_SLICE: case B_FREE_SLICE:
            return EmitSlicePool(c, an, ln);
        case B_FREE: {
            auto lv = RecvLoc(an[0]);
            assert(!lv.fl.empty());
            // A freelist entry will become an unchecked element address at
            // allocation, so only an existing slot may enter it. Evaluate
            // the argument once, then use the ordinary array bounds check
            // (including its unsigned comparison for negative/large indices).
            auto x = GenPure(an[1]);
            auto i = T();
            L("int64_t ", i, " = GS_IDX(", x, ", ", lv.lenlv, ", ", LocArgs(ln), ");");
            L("*(gs_i64 *)", Top(lv.flstk), " = ", i, ";");
            L(TopW(lv.flstk), " += 8;");
            L(lv.fl, ".len++;");
            return {};
        }
        default:
            Fail(ln, cat("builtin not implemented: ", builtindefs[c->builtin].name));
    }
}

// The bytes a literal of fixed type t stores, value-bearing ones only (pads
// are skipped), when the literal and every part of it is a constant whose
// image is known here; false otherwise.
inline bool CodeGen::LiteralBytes(Node *n, TypeExpr *t, vector<uint8_t> &out) {
    if (!n || !t || !IsFix(t)) return false;
    auto put = [&](uint64_t v, int64_t size) {
        for (int64_t i = 0; i < size; i++) out.push_back((uint8_t)(v >> (8 * i)));
    };
    if (Is<NullLit>(n)) {
        // The null of every optional reference is all zero bytes: a null
        // pointer, a fat reference's { 0, 0 }, a relative offset of 0.
        if (t->kind != TY_REF || !t->ref->optional) return false;
        put(0, FixedSize(t));
        return true;
    }
    if (n->exprtype && !TEq(n->exprtype, t)) return false;
    switch (t->kind) {
        case TY_INT: {
            auto i = Is<IntLit>(n);
            if (!i || t->intstorage == IS_VARINT) return false;
            put((uint64_t)i->val, IntSize(t->intstorage));
            return true;
        }
        case TY_BOOL: {
            auto b = Is<BoolLit>(n);
            if (!b) return false;
            put(b->val ? 1 : 0, 1);
            return true;
        }
        case TY_FLT: {
            auto f = Is<FltLit>(n);
            if (!f) return false;
            uint64_t bits = 0;
            if (t->fltstorage == FS_F32) {
                auto v = (float)f->val;
                uint32_t b32;
                memcpy(&b32, &v, 4);
                bits = b32;
                put(bits, 4);
            } else {
                memcpy(&bits, &f->val, 8);
                put(bits, 8);
            }
            return true;
        }
        case TY_STRUCT: {
            auto sl = Is<StructLit>(n);
            auto si = SI(t);
            if (!sl || sl->sinst != si) return false;
            for (size_t fi = 0; fi < si->st->fields.size(); fi++) {
                if (si->st->fields[fi].ispad) continue;
                auto init = sl->InitFor((int)fi);
                auto ft = si->ftypes[fi];
                // An omitted field is an optional reference left null.
                if (!init) {
                    if (ft->kind != TY_REF || !ft->ref->optional) return false;
                    put(0, FixedSize(ft));
                } else if (!LiteralBytes(init, ft, out)) {
                    return false;
                }
            }
            return true;
        }
        case TY_ARRAY: {
            auto al = Is<ArrayLit>(n);
            if (!al || t->arr->akind != A_FIXED) return false;
            auto k = ArrSize(t->arr);
            if (al->fillval) {
                for (int64_t e = 0; e < k; e++)
                    if (!LiteralBytes(al->fillval, t->arr->sub, out)) return false;
                return true;
            }
            if ((int64_t)al->elems.size() != k) return false;
            for (auto e : al->elems)
                if (!LiteralBytes(e, t->arr->sub, out)) return false;
            return true;
        }
        default: return false;
    }
}

// Whether every value-bearing byte a fill of literal n stores into slots of
// type t is the same byte, which a memset can then write.
inline bool CodeGen::UniformFillByte(Node *n, TypeExpr *t, int &byte) {
    vector<uint8_t> img;
    if (!LiteralBytes(n, t, img) || img.empty()) return false;
    for (auto b : img) if (b != img[0]) return false;
    byte = img[0];
    return true;
}

// The element `n` a push or an alloc adds to an array of `elem`, as far as
// it goes before its slot is claimed. The receiver is evaluated, then the
// argument, then the element is added (§2), and the argument may itself
// grow the array. A fixed-size element is therefore evaluated here, so that
// it follows whatever the argument added and the returned reference names
// it, and a relative-reference element is the plain reference its slot
// encodes. A variable-size element, and a fixed one holding relative
// references of either form (a self-relative offset measures from where the
// element lives, an `in pool` `self` is its position in the pool), are built
// at the slot instead and give nothing here; the checker keeps the array
// from growing while such a value is under construction (§1.3,
// BuiltInPlace).
inline string CodeGen::ElemValue(Node *n, TypeExpr *elem) {
    if (IsRelRef(elem)) {
        auto ev = T();
        L("uint8_t *", ev, " = (uint8_t *)(", GenX(n), ");");
        return ev;
    }
    if (IsBytesT(elem) || HasRelRef(elem)) return "";
    // A local variable keeps its value up to the store: only the array's
    // own bookkeeping runs in between.
    auto x = GenXD(n, elem);
    return Is<Ident>(n) && IsCName(x) ? x : Snapshot(elem, x);
}

// Writes the fixed-size element `n`, given what ElemValue made of it, into
// the claimed slot the typed pointer `e` names.
inline void CodeGen::StoreElemAt(Node *n, TypeExpr *elem, const string &e, const string &ev,
                                 Line ln) {
    // A relative-reference element stores the offset from its own slot,
    // not the pointer (§3.9).
    if (IsRelRef(elem))
        EmitRelStoreAt(cat("(uint8_t *)", e), elem, ev, ln, true, RelValue(n));
    else if (ev.empty()) GenAny(n, Dst { DK_LVALUE, cat("(*", e, ")"), elem });
    else StoreWhole(e, elem, ev);
}

inline vector<string> CodeGen::EmitPush(vector<Node *> &an, Line ln) {
    auto lv = RecvLoc(an[0]);
    auto v = ArrayView(lv);
    auto elem = v.elem;
    auto ak = lv.t->arr->akind;
    auto ev = ElemValue(an[1], elem);
    string ref;
    if (ak == A_LIMITED) {
        auto nl = T();
        L("int64_t ", nl, " = ", v.len, ";");
        L("if (", nl, " >= ", LimitedCap(lv), ") gs_abort(GS_E_CAPACITY, ", LocArgs(ln), ");");
        auto e = T();
        L(CT(elem), " *", e, " = (", CT(elem), " *)(", ElemAddr(v, nl), ");");
        StoreElemAt(an[1], elem, e, ev, ln);
        L(v.lenlv, " = (", LenCast(lv), ")(", nl, " + 1);");
        ref = e;
    } else {
        assert(!lv.stk.empty());
        NoteLen(lv.stk, v.lenlv, lv.lenroot);
        // A value evaluated ahead goes out at the top, and the element is
        // then the one just below it: a read of the top a destination takes
        // at once, and an operand followed by statements into a temporary
        // (GenOperandVal), as a pop's value is.
        if (!ev.empty() && !IsRelRef(elem)) {
            EmitValStore(lv.stk, elem, ev);
            L(v.lenlv, "++;");
            ref = cat("((", CT(elem), " *)(", Top(lv.stk), " - ", FixedSize(elem), "))");
            return { NewElemResult(ref, elem, lv, ln) };
        }
        auto e = T();
        if (IsBytesT(elem)) {
            L("uint8_t *", e, " = ", Top(lv.stk), ";");
        } else {
            L(CT(elem), " *", e, " = (", CT(elem), " *)", Top(lv.stk), ";");
        }
        // StoreElemAt's three cases, at the stack's top, which each moves
        // past the element.
        if (IsRelRef(elem))
            EmitRelStore(lv.stk, elem, ev, ln, RelValue(an[1]));
        else if (ev.empty()) GenConstruct(an[1], lv.stk, elem);
        else EmitValStore(lv.stk, elem, ev);
        L(v.lenlv, "++;");
        ref = e;
    }
    return { NewElemResult(ref, elem, lv, ln) };
}

// What push and alloc_ref return for the element just added at `e`, a
// pointer to its slot: a reference to it (§3.3), which a receiver decaying it
// loads from (CallVal0). An element that is itself a reference gives the one
// it holds instead, loaded if relative, as `&` of it does: there are no
// references to references (§3.8).
inline string CodeGen::NewElemResult(const string &e, TypeExpr *elem, const Loc &lv, Line ln) {
    if (elem->kind != TY_REF) return e;
    if (elem->ref->lenstorage >= 0) return LoadLoc(BytesLoc(e, elem, lv), elem, ln);
    return Snapshot(elem, cat("*", e));
}

inline void CodeGen::EmitAppend(vector<Node *> &an, Line ln) {
    auto lv = RecvLoc(an[0]);
    auto v = ArrayView(lv);
    auto elem = v.elem;
    auto ak = lv.t->arr->akind;
    auto src = an[1];
    // Appending copy(x) appends x: the run is a copy of its elements
    // either way.
    if (auto c = Is<Call>(src); c && c->builtin == B_COPY) src = c->FirstArg();
    // append(f()) where f returns a resizable, or a variable array in the
    // element-run form (C.3): the callee emits raw elements at our top and
    // hands back the count -- contiguous by construction (§7.3). A callee
    // with no run form falls back to a value-form call with its length
    // prefix slid out (inside EmitSpecCall). Control expressions, including
    // inlined calls, pass the same destination to each branch.
    auto st = src->exprtype;
    auto asrun = IsResz(st) || (st->kind == TY_ARRAY && st->arr->akind == A_VAR);
    auto fresh = Is<Call>(src) || IsCtl(src);
    if (ak != A_LIMITED) NoteLen(lv.stk, v.lenlv, lv.lenroot);
    if (fresh && asrun && ak != A_LIMITED) {
        auto nn = T();
        L("int64_t ", nn, " = 0;");
        GenAny(src, Dst { DK_STACK, lv.stk, st, nn });
        L(v.lenlv, " += ", nn, ";");
        return;
    }
    if (fresh && st->kind == TY_ARRAY && st->arr->akind == A_LIMITED &&
        ArrSize(st->arr) < 0 && ak != A_LIMITED) {
        // Build the limited result on the receiving stack, then remove its
        // capacity/length header and unused capacity in place. Only its live
        // elements belong to the appended run.
        auto base = T(), nn = T(), bytes = T();
        L("uint8_t *", base, " = ", Top(lv.stk), ";");
        GenAny(src, Dst { DK_STACK, lv.stk, st });
        L("int64_t ", nn, " = *(gs_u32 *)(", base, " + 4);");
        L("int64_t ", bytes, " = ", nn, " * ", FixedSize(elem), ";");
        L("memmove(", base, ", ", base, " + 8, (size_t)", bytes, ");");
        L(TopW(lv.stk), " = ", base, " + ", bytes, ";");
        L(v.lenlv, " += ", nn, ";");
        return;
    }
    // A literal of elements that are not fixed-size, or that hold relative
    // references (measured from where they are written), builds its run
    // where the elements stay (§4.3): at the receiver's top, or in a limited
    // array's free slots, the checker keeping the receiver from growing
    // meanwhile. Other elements are evaluated first, as a pushed fixed-size
    // one is, and copied.
    if (auto al = Is<ArrayLit>(src); al && (IsBytesT(elem) || HasRelRef(elem))) {
        if (IsBytesT(elem)) {
            auto nn = T();
            L("int64_t ", nn, " = 0;");
            GenArrayLit(al, lv.stk, nn);
            L(v.lenlv, " += ", nn, ";");
            return;
        }
        auto count = LitCount(al);
        string ol, at = Top(lv.stk);
        if (ak == A_LIMITED) {
            ol = T();
            L("int64_t ", ol, " = ", v.len, ";");
            L("if (", ol, " + ", count, " > ", LimitedCap(lv), ") gs_abort(GS_E_CAPACITY, ",
              LocArgs(ln), ");");
            at = ElemAddr(v, ol);
        }
        // The run is a fixed array of the literal's type laid over the slots.
        auto rt = CT(src->exprtype);
        auto p = T();
        L(rt, " *", p, " = (", rt, " *)(", at, ");");
        FixedArrayLitAt(al, cat("(*", p, ")"), true);
        if (ak == A_LIMITED) {
            L(v.lenlv, " = (", LenCast(lv), ")(", ol, " + ", count, ");");
        } else {
            Bump(lv.stk, cat(count * FixedSize(elem)));
            L(v.lenlv, " += ", count, ";");
        }
        return;
    }
    auto se = GenSrcElems(src);
    auto nn = T();
    L("int64_t ", nn, " = ", se.n, ";");
    if (ak == A_LIMITED) {
        auto ol = T();
        L("int64_t ", ol, " = ", v.len, ";");
        L("if (", ol, " + ", nn, " > ", LimitedCap(lv), ") gs_abort(GS_E_CAPACITY, ",
          LocArgs(ln), ");");
        L(CopyFn(), "(", ElemAddr(v, ol), ", ", se.elems, ", (size_t)(", nn, " * ",
          FixedSize(elem), "));");
        L(v.lenlv, " = (", LenCast(lv), ")(", ol, " + ", nn, ");");
        return;
    }
    assert(!lv.stk.empty());
    EmitCopyElems(lv.stk, elem, se.elems, nn);
    L(v.lenlv, " += ", nn, ";");
}

inline vector<string> CodeGen::EmitAlloc(Call *c, vector<Node *> &an, Line ln) {
    auto lv = RecvLoc(an[0]);
    assert(!lv.fl.empty() && !lv.stk.empty());
    auto v = ArrayView(lv);
    auto elem = v.elem;
    auto esz = FixedSize(elem);
    // The element is evaluated ahead of the freelist bookkeeping, or built
    // at the slot once that is known, as a pushed one is (ElemValue).
    auto ev = ElemValue(an[1], elem);
    // A freelist slot is taken before an element built at it runs its
    // initializers, so nothing they free can change which one it is. A
    // fresh slot at the top joins the array only once the element is
    // written, as a pushed one does: until then no index reaches it, and the
    // checker keeps the array from growing into it meanwhile (§1.3(4)).
    // Freed slots all lie below the length, since a pool never shrinks, so
    // the index tells which kind was taken.
    auto iv = T();
    L("int64_t ", iv, ";");
    L("if (", lv.fl, ".len > 0) {");
    ind++;
    L(lv.fl, ".len--;");
    L(TopW(lv.flstk), " -= 8;");
    L(iv, " = *(gs_i64 *)", Top(lv.flstk), ";");
    ind--;
    L("} else {");
    ind++;
    L(iv, " = ", lv.lenlv, ";");
    ind--;
    L("}");
    auto e = T();
    L(CT(elem), " *", e, " = (", CT(elem), " *)(", ElemAddr(v, iv), ");");
    StoreElemAt(an[1], elem, e, ev, ln);
    L("if (", iv, " == ", lv.lenlv, ") {");
    ind++;
    L(lv.lenlv, "++;");
    L(TopW(lv.stk), " += ", esz, ";");
    ind--;
    L("}");
    if (c->builtin == B_ALLOC_INDEX) return { iv };
    return { NewElemResult(e, elem, lv, c->line) };
}

// A slice pool (§5.4): the element region grows like any grow-only array's,
// and the runtime's gs_spans_* keep the freelist of (index, count) spans.
inline vector<string> CodeGen::EmitSlicePool(Call *c, vector<Node *> &an, Line ln) {
    auto lv = RecvLoc(an[0]);
    assert(!lv.fl.empty() && !lv.stk.empty());
    auto v = ArrayView(lv);
    auto elem = v.elem;
    auto esz = FixedSize(elem);
    assert(esz > 0);   // No element is zero-size (§3.4).
    // A slice handed back becomes an index into the pool. An empty one can be
    // a default slice pointing at no storage at all; with no cells to free or
    // keep, index 0 serves it. A non-empty one the checker rooted at this pool
    // exactly starts a whole number of elements into the length; any other
    // one is checked to, and to end inside the length (§5.4).
    auto indexof = [&](const string &sv) {
        auto i = T();
        if (!c->poolcheck) {
            L("int64_t ", i, " = ", sv, ".len ? ((uint8_t *)", sv, ".data - (uint8_t *)", v.elems,
              ") / ", esz, " : 0;");
            return i;
        }
        L("int64_t ", i, " = 0;");
        L("if (", sv, ".len) {");
        ind++;
        auto off = T();
        L("uint64_t ", off, " = (uint64_t)((uintptr_t)", sv, ".data - (uintptr_t)", v.elems, ");");
        L("if (", off, " % ", esz, " || ", off, " / ", esz, " >= (uint64_t)", lv.lenlv,
          " || (uint64_t)", sv, ".len > (uint64_t)", lv.lenlv, " - ", off, " / ", esz,
          ") gs_abort(GS_E_POOLSLICE, ", LocArgs(ln), ");");
        L(i, " = (int64_t)(", off, " / ", esz, ");");
        ind--;
        L("}");
        return i;
    };
    if (c->builtin == B_FREE_SLICE) {
        auto sv = GenPure(an[1]);
        L("gs_spans_free(", SpanArgs(lv), ", ", indexof(sv), ", ", sv, ".len);");
        return {};
    }
    string i, n;
    if (c->builtin == B_ALLOC_SLICE) {
        n = SliceLen(an[1], elem, ln);
        i = T();
        L("int64_t ", i, " = ", PlaceRun(lv, n), ";");
        EmitSliceExtend(lv, cat(i, " + ", n), esz);
        EmitDefaultElems(v, i, n, c->defaultinit);
    } else {
        auto sv = GenPure(an[1]);
        n = SliceLen(an[2], elem, ln);
        i = indexof(sv);
        auto ol = T();
        L("int64_t ", ol, " = ", sv, ".len;");
        L("if (", n, " <= ", ol, ") {");
        ind++;
        L("gs_spans_free(", SpanArgs(lv), ", ", i, " + ", n, ", ", ol, " - ", n, ");");
        ind--;
        L("} else {");
        ind++;
        // Growth stays in place where the slice ends the array or free
        // elements follow it. Otherwise the slice moves where alloc_slice
        // would put the grown run, with its own place freed first so that,
        // merged with free elements beside it, it can be that place; the
        // copy then overlaps its source. An empty slice has nothing to keep
        // in place, so it is always placed like a new run.
        L("if (", ol, " == 0) {");
        ind++;
        L(i, " = ", PlaceRun(lv, n), ";");
        ind--;
        L("} else if (", i, " + ", ol, " != ", lv.lenlv, ") {");
        ind++;
        auto ni = T();
        L("int64_t ", ni, " = gs_spans_regrow(", SpanArgs(lv), ", ", lv.lenlv, ", ", i, ", ", ol,
          ", ", n, ");");
        L("if (", ni, " != ", i, ") memmove(", ElemAddr(v, ni), ", ", ElemAddr(v, i),
          ", (size_t)(", ol, " * ", esz, "));");
        L(i, " = ", ni, ";");
        ind--;
        L("}");
        EmitSliceExtend(lv, cat(i, " + ", n), esz);
        EmitDefaultElems(v, cat(i, " + ", ol), cat(n, " - ", ol), c->defaultinit);
        ind--;
        L("}");
    }
    auto r = T();
    auto sct = CT(ast.SliceOf(elem, ln)), ect = CT(elem);
    L(sct, " ", r, " = { (", ect, " *)(", ElemAddr(v, i), "), ", n, " };");
    return { r };
}

// Where a slice pool places a run of n elements: past the end of the array
// while the freelist is empty, as it stays in a pool nothing is freed from,
// and otherwise where the runtime finds room.
inline string CodeGen::PlaceRun(const Loc &lv, const string &n) {
    return cat("(", lv.fl, ".len ? gs_spans_alloc(", SpanArgs(lv), ", ", lv.lenlv, ", ", n,
               ") : ", lv.lenlv, ")");
}

// The freelist as the gs_spans_* helpers take it: its base, its node count
// and its stack's top, which they move.
inline string CodeGen::SpanArgs(const Loc &lv) {
    return cat(lv.fl, ".base, &", lv.fl, ".len, &(", TopW(lv.flstk), ")");
}

// A slice pool's length argument, evaluated once. A negative length, or one
// no data stack could hold, aborts before anything changes.
inline string CodeGen::SliceLen(Node *n, TypeExpr *elem, Line ln, const char *error,
                                Node *msg) {
    auto nv = T();
    L("int64_t ", nv, " = (int64_t)(", GenX(n), ");");
    auto esz = FixedSize(elem);
    if (esz)
        L("if ((uint64_t)", nv, " > GS_STACK_RESERVE / ", esz, ") ", FailCall(error, msg, ln), ";");
    else
        L("if (", nv, " < 0) ", FailCall(error, msg, ln), ";");
    return nv;
}

// The call a failed check makes: the runtime's message for `error`, or the
// string literal a range_index or check_length was given in its place.
inline string CodeGen::FailCall(const char *error, Node *msg, Line ln) {
    if (auto s = msg ? Is<StrLit>(msg) : nullptr)
        return cat("gs_abort_msg((const uint8_t *)", CStr(s->val), ", ", s->val.size(), ", ",
                   LocArgs(ln), ")");
    return cat("gs_abort(", error, ", ", LocArgs(ln), ")");
}

// Grows a slice pool's element region to `end` elements where it is shorter.
inline void CodeGen::EmitSliceExtend(const Loc &lv, const string &end, int64_t esz) {
    auto ext = T();
    L("int64_t ", ext, " = ", end, " - ", lv.lenlv, ";");
    L("if (", ext, " > 0) {");
    ind++;
    L(lv.lenlv, " += ", ext, ";");
    Bump(lv.stk, cat(ext, " * ", esz));
    ind--;
    L("}");
}

// Two checked loop idioms whose zero defaults have no observable per-element
// work: filling a whole slice, and appending from an array's length to an end.
// Field defaults, relative references and arbitrary expressions keep their
// ordinary evaluation order and construction code.
inline bool CodeGen::BulkDefaultLoop(ForLoop *loop) {
    if (loop->idxdef || loop->vdef->captured || loop->vdef->type->kind != TY_INT ||
        loop->vdef->type->intstorage != IS_I64) return false;
    auto loopbody = loop->body;
    if (loopbody->stmts.size() != 1 || loopbody->tail) return false;
    auto unref = [](Node *n) {
        auto u = Is<Unary>(n);
        return u && u->op == T_BITAND ? u->child : n;
    };
    auto lenof = [&](Node *n, Node *array) {
        auto dot = Is<Dot>(n);
        return dot && !dot->IsField() && dot->name == "len" && SamePath(dot->obj, unref(array));
    };
    Node *array = nullptr, *value = nullptr, *end = nullptr;
    auto append = false;
    if (auto a = Is<Assign>(loopbody->stmts[0]); a &&
        (a->op == T_ASSIGN || a->op == T_DOTASSIGN) && loop->iterkind == IK_COUNT) {
        auto index = Is<Index>(a->lval);
        auto id = index ? Is<Ident>(index->idx) : nullptr;
        if (!id || id->vdef != loop->vdef || !lenof(loop->iter, index->obj)) return false;
        array = index->obj; value = a->rhs;
    } else if (auto call = Is<Call>(loopbody->stmts[0]); call &&
               call->builtin == B_PUSH && loop->iterkind == IK_RANGE) {
        auto args = call->ValueArgNodes();
        auto range = Is<RangeExpr>(loop->iter);
        if (args.size() != 2 || !range || !lenof(range->lo, args[0]) ||
            (!Is<Ident>(range->hi) && !Is<IntLit>(range->hi)) ||
            range->exprtype->kind != TY_INT || range->exprtype->intstorage != IS_I64)
            return false;
        array = args[0]; value = args[1]; end = range->hi; append = true;
    } else return false;
    auto type = unref(array)->exprtype;
    if (type->kind == TY_REF) type = type->ref->sub;
    if (append ? !IsResz(type) || type->kind != TY_ARRAY : type->kind != TY_SLICE) return false;
    auto elem = append ? type->arr->sub : type->sub;
    if (!FieldChainRoot(unref(array), true) || !ZeroDefaultValue(value, elem)) return false;
    auto lv = RecvLoc(array);
    auto view = ArrayView(lv);
    auto esz = FixedSize(elem);
    if (append) {
        NoteLen(lv.stk, view.lenlv, lv.lenroot);
        auto first = T(), limit = T();
        L("int64_t ", first, " = ", view.len, ";");
        L("int64_t ", limit, " = ", GenX(end), ";");
        L("if (", limit, " > ", first, ") {");
        ind++;
        // The loop would have run into the guard gap; report it the same way.
        L("if ((uint64_t)", limit, " > GS_STACK_RESERVE / ", esz, ") gs_stack_overflow(",
          Top(lv.stk), ");");
        L("GS_MEMZERO(", Top(lv.stk), ", (size_t)((", limit, " - ", first, ") * ", esz, "));");
        Bump(lv.stk, cat("(", limit, " - ", first, ") * ", esz));
        L(view.lenlv, " = ", limit, ";");
        ind--;
        L("}");
    } else {
        L("if (", view.len, ") GS_MEMZERO(", view.elems, ", (size_t)(", view.len, " * ", esz, "));");
    }
    return true;
}

// Default values (§4.2) for `count` elements of an array view from index
// `first`: one clear where the default is all zero bytes, else each built.
inline void CodeGen::EmitDefaultElems(const ArrView &v, const string &first,
                                      const string &count, Node *init) {
    auto esz = FixedSize(v.elem);
    if (!HasFieldDefaults(v.elem)) {
        L("GS_MEMZERO(", ElemAddr(v, cat("(", first, ")")), ", (size_t)((", count, ") * ", esz,
          "));");
        return;
    }
    auto k = T();
    L("for (int64_t ", k, " = 0; ", k, " < ", count, "; ", k, "++) {");
    ind++;
    auto e = T();
    L(CT(v.elem), " *", e, " = (", CT(v.elem), " *)(", ElemAddr(v, cat("(", first, " + ", k, ")")),
      ");");
    PushSc(SC_PLAIN);
    GenAny(init, Dst { DK_LVALUE, cat("(*", e, ")"), v.elem });
    PopSc();
    ind--;
    L("}");
}

// The image of a resizable at the top of `stk`: a frame object's fixed
// fields are the bytes before its innermost tail header, any other shape's
// the static prefix EmitRzCopy walks.
inline void CodeGen::EmitRzImage(Loc src, TypeExpr *t, const string &stk, Line ln) {
    if (IsFrameObj(t)) {
        if (!src.val) src = FoView(src);
        auto th = FoTailHdr(t, src.s);
        auto cnt = T();
        L("int64_t ", cnt, " = ", th, ".len;");
        L("GS_MEMCPY(", Top(stk), ", &", cnt, ", 8);");
        Bump(stk, "8");
        auto pre = FoPrefixSize(t);
        L("GS_MEMCPY(", Top(stk), ", &", src.s, ", ", pre, ");");
        Bump(stk, pre);
        EmitCopyElems(stk, FoTailArr(t)->arr->sub, cat(th, ".base"), cat(th, ".len"));
        return;
    }
    auto cntp = T();
    L("uint8_t *", cntp, " = ", Top(stk), ";");
    auto lenv = T();
    L("int64_t ", lenv, ";");
    Bump(stk, "8");
    EmitRzCopy(src, t, stk, lenv, ln);
    L("GS_MEMCPY(", cntp, ", &", lenv, ", 8);");
}

// The globals a thread program can name (CheckThreadGlobals admits flat
// ones only), in declaration order: read-only static data, spelled out or
// shared, is not among them, since every instance reads it in place.
inline vector<VarDef *> &CodeGen::ThreadGlobals(FnSpec *entry) {
    auto it = threadglobals.find(entry);
    if (it != threadglobals.end()) return it->second;
    set<FnSpec *> seen;
    set<VarDef *> named;
    set<TypeExpr *> namedtypes;
    function<void(FnSpec *)> rec = [&](FnSpec *sp) {
        if (!sp || !sp->body || !seen.insert(sp).second) return;
        function<void(Node *)> walk = [&](Node *n) {
            if (!n) return;
            NodeNamedArrays(n, namedtypes, [&](VarDef *a, bool) { named.insert(a); });
            if (auto id = Is<Ident>(n))
                if (auto v = id->vdef; v && v->isglobal) named.insert(v);
            if (auto c = Is<Call>(n)) {
                rec(c->spec);
                for (auto d : c->dispatch) rec(d);
                for (auto &fs : c->fmtspecs) rec(fs.second);
            }
            RunChildren(n, walk);
        };
        walk(sp->body);
    };
    rec(entry);
    auto &out = threadglobals[entry];
    for (auto g : ast.globals)
        for (auto d : g->defs)
            if (named.count(d) && !gstatic.count(d) && !gshared.count(d)) out.push_back(d);
    return out;
}

// thread_spawn(worker, args...) and thread_spawn_contained: the arguments
// constructed contiguously, then the worker program's globals as copies of
// this instance's, each as [int64 size][image] (§11.2); the thunk unpacks
// them into the worker's fresh instance.
inline vector<string> CodeGen::EmitThreadSpawn(Call *c, vector<Node *> &an) {
    usesthreads = true;
    auto sp = c->spec;
    auto thunk = EnsureThreadThunk(sp);
    string stk;
    auto base = BytesTemp(stk);
    vector<string> channels;
    struct Handoff { string cap, dest; bool pointer; int consume; };
    vector<Handoff> handoffs;
    function<bool(Node *)> stored_pointer = [&](Node *n) {
        if (Is<Ident>(n)) return true;
        if (auto d = Is<Dot>(n); d && d->IsField()) return stored_pointer(d->obj);
        if (auto ix = Is<Index>(n)) return stored_pointer(ix->obj);
        return false;
    };
    for (size_t i = 0; i < sp->argtypes.size(); i++) {
        auto pt = sp->argtypes[i];
        if (pt->kind == TY_NATIVE && pt->native->kind == NK_CHANNEL) {
            auto handle = Snapshot(pt, GenPure(an[1 + i]));
            channels.push_back(handle);
            EmitValStore(stk, pt, handle);
            continue;
        }
        if (IsSharedSendable(pt) && pt->native->kind != NK_THREAD &&
            pt->native->kind != NK_CHANNEL) {
            auto cap = Snapshot(pt, GenPure(an[1 + i]));
            bool pointer = pt->kind == TY_NATIVE && pt->native->kind == NK_POINTER;
            int consume = pointer && !stored_pointer(an[1 + i]);
            auto dest = T();
            L("uint8_t *", dest, " = ", Top(stk), ";");
            handoffs.push_back({cap, dest, pointer, consume});
            EmitValStore(stk, pt, cap);
            continue;
        }
        if (!IsResz(pt)) {
            if (!IsBytesT(pt) &&
                (pt->kind == TY_INT || pt->kind == TY_FLT || pt->kind == TY_BOOL)) {
                // Scalar arguments can follow a byte-sized argument too.
                auto v = T();
                FixedLocal(pt, v, GenXD(an[1 + i], pt));
                L("GS_MEMCPY(", Top(stk), ", &", v, ", ", FixedSize(pt), ");");
                Bump(stk, cat(FixedSize(pt)));
            } else GenConstruct(an[1 + i], stk, pt);
            continue;
        }
        // Resizable values have an out-of-line header. Transfer a flat
        // image with its count, never a pointer into the spawning instance.
        // Packet metadata is byte packed: keep counts in scalar locals and
        // copy them to/from saved byte addresses, without adding padding.
        auto szp = T();
        L("uint8_t *", szp, " = ", Top(stk), ";");
        Bump(stk, "8");
        auto cntp = T();
        L("uint8_t *", cntp, " = ", Top(stk), ";");
        Bump(stk, "8");
        auto cnt = T();
        L("int64_t ", cnt, " = 0;");
        if (IsFrameObj(pt)) {
            // Reserve the packed prefix, construct directly into the
            // packet, then save only the header's count and fixed fields.
            auto pre = FoPrefixSize(pt), pp = T(), h = T();
            L("uint8_t *", pp, " = ", Top(stk), ";");
            Bump(stk, pre);
            L(CT(pt), " ", h, ";");
            GenConstruct(an[1 + i], stk, pt, h);
            L(cnt, " = ", FoTailHdr(pt, h), ".len;");
            L("GS_MEMCPY(", pp, ", &", h, ", ", pre, ");");
        } else {
            GenConstruct(an[1 + i], stk, pt, cnt);
        }
        L("GS_MEMCPY(", cntp, ", &", cnt, ", 8);");
        auto sz = T();
        L("int64_t ", sz, " = ", Top(stk), " - (", szp, " + 8);");
        L("GS_MEMCPY(", szp, ", &", sz, ", 8);");
    }
    for (auto d : ThreadGlobals(sp)) {
        auto szp = T();
        L("uint8_t *", szp, " = ", Top(stk), ";");
        Bump(stk, "8");
        auto lv = VarLoc(d);
        if (IsResz(d->type)) {
            EmitRzImage(lv, d->type, stk, c->line);
            if (d->reusable) {
                // The pool's freelist follows: its count, then its entries.
                auto &p = gpools[d];
                auto flsz = FlEntrySize(d);
                auto cnt = T();
                L("int64_t ", cnt, " = ", p.first, ".len;");
                L("GS_MEMCPY(", Top(stk), ", &", cnt, ", 8);");
                Bump(stk, "8");
                L("GS_MEMCPY(", Top(stk), ", ", p.first, ".base, (size_t)(", p.first,
                  ".len * ", flsz, "));");
                Bump(stk, cat(p.first, ".len * ", flsz));
            }
        } else if (IsBytesT(d->type)) {
            auto n = T();
            L("int64_t ", n, " = ", SizeX(d->type, lv.s), ";");
            L("GS_MEMCPY(", Top(stk), ", ", lv.s, ", (size_t)", n, ");");
            Bump(stk, n);
        } else {
            L("GS_MEMCPY(", Top(stk), ", &", lv.s, ", ", FixedSize(d->type), ");");
            Bump(stk, cat(FixedSize(d->type)));
        }
        auto sz = T();
        L("int64_t ", sz, " = ", Top(stk), " - (", szp, " + 8);");
        L("GS_MEMCPY(", szp, ", &", sz, ", 8);");
    }
    // A later argument may itself spawn. Prepare no TLS pending leases
    // until all Goose evaluation is complete, so nested spawns cannot take
    // the outer packet's claims. Patch pointer fields to the distinct claims
    // only after retaining them; typed views/atomic fields keep their image.
    for (auto &h : handoffs) {
        auto worker = T();
        L("gs_shared_cap ", worker, " = gs_shared_handoff((gs_shared_cap){", h.cap,
          ".slot, ", h.cap, ".generation}, ", h.consume, ", ", LocArgs(c->line), ");");
        if (h.pointer)
            L("GS_MEMCPY(", h.dest, ", &", worker, ", sizeof ", worker, ");");
    }
    for (auto &channel : channels)
        L("gs_channel_handoff(", channel, ", ", LocArgs(c->line), ");");
    auto id = T();
    auto structured = c->builtin == B_THREAD_SPAWN_JOIN ||
                      c->builtin == B_THREAD_SPAWN_CONTAINED_JOIN;
    auto contained = c->builtin == B_THREAD_SPAWN_CONTAINED ||
                     c->builtin == B_THREAD_SPAWN_CONTAINED_JOIN;
    L(structured ? "gs_handle " : "int64_t ", id, " = ",
      structured ? "gs_thread_spawn_structured(" : "gs_thread_spawn(",
      thunk, ", ", base, ", ", Top(stk), " - ", base, contained ? ", 1);" : ", 0);");
    return { id };
}

// The worker's entry thunk, by name; its body follows once every thread
// program's stack count is known (EmitThreadThunk, from EmitProgramInit).
inline string CodeGen::EnsureThreadThunk(FnSpec *sp) {
    auto it = thunks.find(sp);
    if (it != thunks.end()) return it->second;
    auto name = Unique(cat("gs_tmain_", Sanitize(sp->sf->ns, sp->sf->name)));
    thunks[sp] = name;
    Append(protos, "static void ", name, "(uint8_t *p);\n");
    return name;
}

// The worker's entry: opens the thread program's block of `stacks` data
// stacks, unpacks the arguments, then gives the thread a fresh instance of
// the globals filled from the spawn image, and runs the body. The runtime
// frees the instance (gs_thread_release), and releases its stacks with the
// thread's others.
inline void CodeGen::EmitThreadThunk(FnSpec *sp, int64_t stacks) {
    auto name = thunks[sp];
    auto &ki = sinfo[sp];
    string b;
    Append(b, "static void ", name, "(uint8_t *p) {\n    gs_stack_block(", stacks, ");\n");
    vector<string> args;
    int regions = 0;    // The dedicated stacks the thunk reserves (thunkregions).
    for (size_t i = 0; i < sp->argtypes.size(); i++) {
        auto pt = sp->argtypes[i];
        if (IsResz(pt)) {
            EmitCoreTypes();
            auto a = cat("a", i), stk = cat(a, "_stk");
            regions++;
            Append(b, "    gs_stack ", stk, "; gs_stack_init(&", stk, ");\n",
                   "    ", RzCT(pt), " ", a, ";\n",
                   "    {\n        int64_t sz; GS_MEMCPY(&sz, p, 8); p += 8;\n");
            auto pre = IsFrameObj(pt) ? FoPrefixSize(pt) : string("0");
            auto hdr = IsFrameObj(pt) ? FoTailHdr(pt, a) : a;
            if (IsFrameObj(pt))
                Append(b, "        GS_MEMCPY(&", a, ", p + 8, ", pre, ");\n");
            Append(b, "        ", hdr, ".base = ", stk, ".top;\n",
                   "        GS_MEMCPY(&", hdr, ".len, p, 8);\n",
                   "        GS_MEMCPY(", stk, ".top, p + 8 + ", pre,
                   ", (size_t)(sz - 8 - ", pre, "));\n",
                   "        ", stk, ".top += sz - 8 - ", pre, "; p += sz;\n    }\n");
            args.push_back(a);
            args.push_back(cat("&", stk));
        } else if (IsBytesT(pt)) {
            Append(b, "    uint8_t *a", i, " = p;\n");
            // Advance past the value; a size fn may be emitted on demand.
            Append(b, "    p += ", SizeX(pt, cat("a", i)).c_str(), ";\n");
            args.push_back(cat("a", i));
        } else if (IsLargeFixed(pt)) {
            // The spawn packet belongs exclusively to this worker, so its
            // fixed argument bytes are already the callee's private copy.
            Append(b, "    ", CT(pt), " *a", i, " = (", CT(pt), " *)p; p += ",
                   FixedSize(pt), ";\n");
            args.push_back(cat("a", i));
        } else if (!FixedSize(pt)) {
            // A value of no bytes (§3.4): the image holds none to fill the
            // object C gives it.
            Append(b, "    ", CT(pt), " a", i, " = {0};\n");
            args.push_back(cat("a", i));
        } else {
            Append(b, "    ", CT(pt), " a", i, "; GS_MEMCPY(&a", i, ", p, ",
                   FixedSize(pt), "); p += ", FixedSize(pt), ";\n");
            PushArg(args, pt, IsPoolParam(sp, i), cat("a", i));
        }
    }
    assert(ki.freevars.empty() && !ki.hasrf && sp->rets.size() <= 1);
    string result, resultstk, resultbase, resultlen;
    if (!sp->rets.empty()) {
        auto rt = sp->rets[0];
        result = "gs_worker_result";
        if (IsResz(rt)) {
            regions++;
            resultstk = "gs_worker_result_stk"; resultbase = "gs_worker_result_base";
            Append(b, "    gs_stack ", resultstk, "; gs_stack_init(&", resultstk, ");\n",
                   "    uint8_t *", resultbase, " = ", resultstk, ".top;\n");
            args.push_back(cat("&", resultstk));
            if (IsFrameObj(rt)) {
                Append(b, "    ", CT(rt), " ", result, " = {0};\n");
                args.push_back(cat("&", result));
            } else {
                resultlen = "gs_worker_result_len";
                Append(b, "    int64_t ", resultlen, " = 0;\n");
                args.push_back(cat("&", resultlen));
            }
        } else if (IsBytesT(rt)) {
            regions++;
            resultstk = "gs_worker_result_stk"; resultbase = "gs_worker_result_base";
            Append(b, "    gs_stack ", resultstk, "; gs_stack_init(&", resultstk, ");\n",
                   "    uint8_t *", resultbase, " = ", resultstk, ".top;\n");
            args.push_back(cat("&", resultstk));
        } else if (ki.cret < 0) {
            if (IsLargeFixed(rt)) {
                regions++;
                resultstk = "gs_worker_result_stk";
                auto ptr = cat(result, "_ptr");
                Append(b, "    gs_stack ", resultstk, "; gs_stack_init(&", resultstk, ");\n",
                       "    ", CT(rt), " *", ptr, " = (", CT(rt), " *)", resultstk, ".top;\n",
                       "    ", resultstk, ".top += sizeof(*", ptr, ");\n");
                result = cat("(*", ptr, ")");
            } else Append(b, "    ", CT(rt), " ", result, " = {0};\n");
            args.push_back(cat("&", result));
        }
    }
    if (ki.needssp) args.push_back("0");
    // A worker has no caller: its function's failures report its declaration.
    if (ki.located) args.push_back(CallerLoc(sp->sf->line));
    Append(b, "    gs_gl = gs_aligned_calloc(sizeof(gs_globals_t), ",
              std::max<int64_t>(gblockalign, 8), ");\n"
              "    if (!gs_gl) gs_panic(\"out of memory copying globals\");\n");
    for (auto d : ThreadGlobals(sp)) {
        auto gn = gnames[d];
        Append(b, "    {\n        int64_t sz; GS_MEMCPY(&sz, p, 8); p += 8; uint8_t *img = p; p += sz;\n");
        if (IsResz(d->type)) {
            auto stk = gstks[d];
            regions++;
            Append(b, "        gs_stack_init(", stk, ");\n");
            if (IsFrameObj(d->type)) {
                auto th = FoTailHdr(d->type, gn);
                auto pre = FoPrefixSize(d->type);
                Append(b, "        GS_MEMCPY(&", gn, ", img + 8, ", pre, ");\n",
                       "        ", th, ".base = ", stk, "->top;\n",
                       "        GS_MEMCPY(&", th, ".len, img, 8);\n",
                       "        GS_MEMCPY(", stk, "->top, img + 8 + ", pre, ", (size_t)(sz - 8 - ",
                       pre, "));\n",
                       "        ", stk, "->top += sz - 8 - ", pre, ";\n");
            } else if (d->reusable) {
                // [count][elements][freelist count][entries]: fixed-size
                // elements, so the element bytes are the count's.
                auto &p = gpools[d];
                auto esz = FixedSize(d->type->arr->sub);
                auto flsz = FlEntrySize(d);
                regions++;
                Append(b, "        int64_t cnt; GS_MEMCPY(&cnt, img, 8);\n",
                       "        int64_t ebytes = cnt * ", esz, ";\n",
                       "        ", gn, ".base = ", stk, "->top;\n",
                       "        ", gn, ".len = cnt;\n",
                       "        GS_MEMCPY(", stk, "->top, img + 8, (size_t)ebytes);\n",
                       "        ", stk, "->top += ebytes;\n",
                       "        gs_stack_init(", p.second, ");\n",
                       "        ", p.first, ".base = ", p.second, "->top;\n",
                       "        GS_MEMCPY(&", p.first, ".len, img + 8 + ebytes, 8);\n",
                       "        GS_MEMCPY(", p.second, "->top, img + 16 + ebytes, (size_t)(",
                       p.first, ".len * ", flsz, "));\n",
                       "        ", p.second, "->top += ", p.first, ".len * ", flsz, ";\n");
            } else {
                Append(b, "        ", gn, ".base = ", stk, "->top;\n",
                       "        GS_MEMCPY(&", gn, ".len, img, 8);\n",
                       "        GS_MEMCPY(", stk, "->top, img + 8, (size_t)(sz - 8));\n",
                       "        ", stk, "->top += sz - 8;\n");
            }
        } else if (IsBytesT(d->type)) {
            auto stk = gstks[d];
            regions++;
            Append(b, "        gs_stack_init(", stk, ");\n",
                   "        ", gn, " = ", stk, "->top;\n",
                   "        GS_MEMCPY(", stk, "->top, img, (size_t)sz);\n",
                   "        ", stk, "->top += sz;\n");
        } else {
            Append(b, "        GS_MEMCPY(&", gn, ", img, (size_t)sz);\n");
        }
        Append(b, "    }\n");
    }
    string argstr;
    for (size_t i = 0; i < args.size(); i++) Append(argstr, i ? ", " : "", args[i]);
    if (sp->rets.empty()) {
        Append(b, "    ", ki.cname, "(", argstr, ");\n");
    } else {
        auto rt = sp->rets[0];
        if (ki.cret == 0) {
            Append(b, "    ", CT(rt), " ", result, " = ", ki.cname, "(", argstr, ");\n");
        } else {
            Append(b, "    ", ki.cname, "(", argstr, ");\n");
        }
        if (IsResz(rt)) {
            auto pre = IsFrameObj(rt) ? FoPrefixSize(rt) : string("0");
            auto len = IsFrameObj(rt) ? cat(FoTailHdr(rt, result), ".len") : resultlen;
            Append(b, "    int64_t gs_worker_result_bytes = ", resultstk, ".top - ", resultbase, ";\n",
                   "    int64_t gs_worker_result_size = 8 + ", pre,
                   " + gs_worker_result_bytes;\n",
                   "    uint8_t *gs_worker_result_image = malloc((size_t)gs_worker_result_size);\n",
                   "    if (!gs_worker_result_image) gs_panic(\"out of memory publishing structured result\");\n",
                   "    GS_MEMCPY(gs_worker_result_image, &", len, ", 8);\n");
            if (IsFrameObj(rt))
                Append(b, "    GS_MEMCPY(gs_worker_result_image + 8, &", result, ", ", pre, ");\n");
            Append(b, "    GS_MEMCPY(gs_worker_result_image + 8 + ", pre, ", ", resultbase,
                   ", (size_t)gs_worker_result_bytes);\n",
                   "    gs_thread_publish_result(gs_worker_result_image, gs_worker_result_size);\n",
                   "    free(gs_worker_result_image);\n");
        } else if (IsBytesT(rt)) {
            Append(b, "    gs_thread_publish_result(", resultbase, ", ",
                   SizeX(rt, resultbase).c_str(), ");\n");
        } else {
            Append(b, "    gs_thread_publish_result(&", result, ", ", FixedSize(rt), ");\n");
        }
    }
    Append(b, "}\n\n");
    code += b;
    thunkregions[sp] = regions;
}

// ------------------------------------------------------------------
// Serialization (docs/design/serialization.md): to_bytes and bytes_of write
// an array's element region out, from_bytes verifies one back in.

// An image is little-endian by definition (§7 of the design), which every
// target this compiles for is; the test folds away, and exists so that a
// big-endian host fails loudly rather than writing bytes only it can read.
inline void CodeGen::EmitLeCheck(Line ln) {
    EmitCoreTypes();
    L("if (!gs_is_le()) gs_abort(GS_E_ENDIAN, ", LocArgs(ln), ");");
}

// The element region of a to_bytes/bytes_of receiver: a byte pointer, and
// the byte count -- which for variable elements is a walk, since an element
// count says nothing about the span.
inline void CodeGen::PayloadOf(Node *n, string &src, string &sz) {
    auto nt = n->exprtype;
    auto rt = nt->kind == TY_REF ? nt->ref->sub : nt;
    auto elem = rt->kind == TY_SLICE ? rt->sub : rt->arr->sub;
    SrcElems se;
    if (rt->kind == TY_ARRAY || nt->kind == TY_REF) {
        // The receiver as a location, through a reference where it is one;
        // GenSrcElems is for the value forms it does not reach.
        auto v = ArrayView(RecvLoc(n));
        auto cnt = T();
        L("int64_t ", cnt, " = ", v.len, ";");
        se.elems = v.elems;
        se.n = cnt;
    } else {
        se = GenSrcElems(n);
    }
    src = T();
    L("const uint8_t *", src, " = (const uint8_t *)(", se.elems, ");");
    sz = T();
    if (IsFix(elem)) {
        L("int64_t ", sz, " = (", se.n, ") * ", FixedSize(elem), ";");
    } else {
        auto i = T();
        L("int64_t ", sz, " = 0;");
        L("for (int64_t ", i, " = 0; ", i, " < (", se.n, "); ", i, "++) ", sz, " += ",
          SizeFn(elem), "(", src, " + ", sz, ");");
    }
}

// `n` bytes at `src` appended to a growable u8 array, in the two shapes
// format appends text to: a resizable writes at its stack top, a limited
// array copies under a capacity check.
inline void CodeGen::AppendBytes(const Loc &lv, const string &src, const string &n, Line ln) {
    auto v = ArrayView(lv);
    if (lv.t->arr->akind == A_LIMITED) {
        auto ol = T();
        L("int64_t ", ol, " = ", v.len, ";");
        L("if (", ol, " + ", n, " > ", LimitedCap(lv), ") gs_abort(GS_E_CAPACITY, ",
          LocArgs(ln), ");");
        L(CopyFn(), "(", ElemAddr(v, ol), ", ", src, ", (size_t)", n, ");");
        L(v.lenlv, " = (", LenCast(lv), ")(", ol, " + ", n, ");");
        return;
    }
    L(CopyFn(), "(", Top(lv.stk), ", ", src, ", (size_t)", n, ");");
    Bump(lv.stk, n);
    L(v.lenlv, " += ", n, ";");
}

// The destination a resizable or variable builtin result is built at, in the
// shapes §7.3 admits: the caller's header, a value slot that takes a length
// prefix in front of the elements, or a fresh temporary when the result has
// no destination of its own. `elems` is where the elements start.
inline CodeGen::RzDest CodeGen::OpenRzDest(TypeExpr *t, Dst d0, Line ln, const char *what) {
    EmitCoreTypes();
    RzDest rd;
    auto resz = IsResz(t);
    rd.stk = d0.s;
    rd.lenlv = d0.lenlv;
    if (d0.k != DK_STACK) {
        if (resz) {
            rd.hdr = RzTemp(t, rd.stk);
            rd.lenlv = RzLenLv(t, rd.hdr);
        } else {
            rd.hdr = BytesTemp(rd.stk);   // a bytes value: its base pointer
        }
    }
    if (rd.lenlv.empty()) {
        // A value slot: the count goes into a length prefix reserved in front
        // of the elements, in the slot's own length storage where the
        // destination has one and the result's otherwise.
        auto at = d0.t && d0.t->kind == TY_ARRAY && d0.t->arr->akind == A_VAR ? d0.t
                  : resz ? nullptr : t;
        if (!at) Fail(ln, cat(what, "() needs a resizable or variable-array destination"));
        rd.ls = LenStore(at->arr);
        rd.pref = T();
        L("uint8_t *", rd.pref, " = ", Top(rd.stk), ";");
        Bump(rd.stk, cat(PrefixBytes(rd.ls)));
    }
    rd.elems = T();
    L("uint8_t *", rd.elems, " = ", Top(rd.stk), ";");
    return rd;
}

inline void CodeGen::CloseRzDest(RzDest &rd, const string &count) {
    if (!rd.pref.empty()) EmitPrefixPatch(rd.pref, rd.ls, rd.stk, count, rd.elems);
    else L(rd.lenlv, " = ", count, ";");
}

// bytes_of(a): the element region as a u8[:], no copy. The view is never
// writable at the language level (§9.5), so the const the payload pointer
// carries is dropped here rather than expressed in the slice type.
inline vector<string> CodeGen::EmitBytesOf(Call *c, vector<Node *> &an, Line ln) {
    EmitLeCheck(ln);
    string src, sz;
    PayloadOf(an[0], src, sz);
    auto s = T();
    L(CT(c->rettypes[0]), " ", s, " = { (uint8_t *)", src, ", ", sz, " };");
    return { s };
}

// to_bytes(a): the image -- a varint byte count, then the element region --
// as a fresh u8[>..], or appended to a builder the caller owns so that its
// own header can go in front. Copying rather than viewing keeps the image
// independent of the array's later growth.
inline vector<string> CodeGen::EmitToBytes(vector<Node *> &an, Dst d0, Line ln) {
    EmitLeCheck(ln);
    string src, sz;
    PayloadOf(an[0], src, sz);
    auto pfx = T(), pn = T();
    L("uint8_t ", pfx, "[10];");
    L("int64_t ", pn, " = gs_uleb_write(", pfx, ", (uint64_t)", sz, ");");
    if (an.size() > 1) {
        auto out = RecvLoc(an[1]);
        AppendBytes(out, pfx, pn, ln);
        AppendBytes(out, src, sz, ln);
        return {};
    }
    auto rd = OpenRzDest(GrowU8(), d0, ln, "to_bytes");
    L("GS_MEMCPY(", Top(rd.stk), ", ", pfx, ", (size_t)", pn, ");");
    Bump(rd.stk, pn);
    L(CopyFn(), "(", Top(rd.stk), ", ", src, ", (size_t)", sz, ");");
    Bump(rd.stk, sz);
    auto tot = T();
    L("int64_t ", tot, " = ", pn, " + ", sz, ";");
    CloseRzDest(rd, tot);
    return rd.hdr.empty() ? vector<string> {} : vector<string> { rd.hdr };
}

// from_bytes<T[...]>(bytes): the framing prefix, then the verifier over the
// payload, then a copy of it into the result's element region. A rejected
// image leaves the array empty, and the bool says which happened.
inline vector<string> CodeGen::EmitFromBytes(Call *c, vector<Node *> &an, Dst d0, Line ln) {
    EmitLeCheck(ln);
    auto t = c->rettypes[0];
    auto elem = t->arr->sub;
    auto sl = GenPure(an[0]);
    auto vf = VerifyFn(elem);
    // The prefix has to account for exactly the rest of the slice: it is what
    // a stream reader sizes its read from, and the first thing here that can
    // say these bytes are not an image at all.
    auto pay = T(), pn = T(), ok = T(), uv = T(), kv = T();
    L("const uint8_t *", pay, " = ", sl, ".data;");
    L("int64_t ", pn, " = 0;");
    L("uint8_t ", ok, " = 0;");
    L("uint64_t ", uv, " = 0;");
    L("int64_t ", kv, " = gs_uleb_check(", sl, ".data, ", sl, ".data + ", sl, ".len, &",
      uv, ");");
    L("if (", kv, " && ", uv, " <= (uint64_t)INT64_MAX && (int64_t)", uv, " == ", sl,
      ".len - ", kv, ") {");
    ind++;
    L(pay, " += ", kv, "; ", pn, " = (int64_t)", uv, "; ", ok, " = 1;");
    ind--;
    L("}");
    string bm = "NULL";
    if (!IsFix(elem) && HasRelRefAny(elem)) {
        // One bit per payload byte: where a variable element starts, which is
        // what the framing pass hands the link pass. Its own stack, so the
        // scratch is gone at the end of the statement -- and an image needing
        // more of that stack than it reserves is one this cannot verify,
        // which is a false rather than a guard-page abort.
        string bstk;
        bm = BytesTemp(bstk);
        auto bn = T();
        L("int64_t ", bn, " = (", pn, " + 7) / 8;");
        L("if (", bn, " > GS_BM_MAX) { ", bn, " = 0; ", ok, " = 0; }");
        L("GS_MEMZERO(", bm, ", (size_t)", bn, ");");
        Bump(bstk, bn);
    }
    auto cnt = T();
    // The verifier reads index types' array lengths through global headers.
    // Those counts may still be held in this function's stack caches.
    set<TypeExpr *> seen;
    string reach;
    NamedArraysIn(elem, seen, [&](VarDef *a, bool) { reach += cat(gstks[a], "\x01"); });
    if (!reach.empty()) MarkFlush(reftops || topdst || topcap ? "*" : reach);
    L("int64_t ", cnt, " = ", ok, " ? ", vf, "(", pay, ", ", pn, ", ", bm, ") : -1;");
    L(ok, " = ", cnt, " >= 0;");
    auto rd = OpenRzDest(t, d0, ln, "from_bytes");
    L("if (", ok, ") {");
    ind++;
    L("GS_MEMCPY(", Top(rd.stk), ", ", pay, ", (size_t)", pn, ");");
    Bump(rd.stk, pn);
    ind--;
    L("}");
    CloseRzDest(rd, cat("(", ok, " ? ", cnt, " : 0)"));
    return { rd.hdr, ok };
}

}  // namespace goose
