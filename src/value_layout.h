// Concrete Goose value layouts shared by native and Wasm lowering.
// Read checked types only. No C emission, type instantiation or ABI naming.
// Representation equality ignores const qualification, as stored layouts do.
#pragma once

namespace goose {

struct ValueLayout {
    int64_t ArrSize(TypeArray *a) {
        assert(a->size >= 0 || !a->sizeexpr);
        return a->size;
    }

    bool TEq(TypeExpr *a, TypeExpr *b);
    StructInst *SI(TypeExpr *t);
    EnumInst *EIOf(TypeExpr *t);
    EnumInst *EIVar(TypeExpr *t);
    // The field runs of a nominal type (ast.h FieldRun); empty for every
    // other kind.
    span<const FieldRun> FieldRuns(TypeExpr *t);
    // As the checker's, over the runs this pass reads rather than builds.
    template<typename F> bool AnyField(TypeExpr *t, F f) { return AnyFieldOf(FieldRuns(t), f); }
    template<typename F> void EachField(TypeExpr *t, F f) { EachFieldOf(FieldRuns(t), f); }
    SizeClass Cls(TypeExpr *t);

    bool IsFix(TypeExpr *t)  { return Cls(t) == SC_FIXED; }
    bool IsResz(TypeExpr *t) { return Cls(t) == SC_RESIZABLE; }
    bool IsRoot(TypeExpr *t) { return Cls(t) == SC_ROOT; }
    bool IsBytesT(TypeExpr *t) { auto c = Cls(t); return c == SC_VARIABLE || c == SC_RESIZABLE; }
    IntStorage LenStore(TypeArray *a);

    static int64_t IntSize(IntStorage s) { return IntBits(s) / 8; }

    IntStorage TagStore(SEnum *en) { return en->variants.size() <= 256 ? IS_U8 : IS_U16; }
    int64_t TagSize(SEnum *en) { return IntSize(TagStore(en)); }

    // Packed layout of a run of fields: byte offsets aligned with the fields
    // vector (pads get their own offset), plus the total size. Fixed types
    // only; the same code computes the static prefix of variable structs.
    struct Layout {
        vector<int64_t> offs;
        int64_t size = 0;
    };
    map<pair<const void *, int>, Layout> layouts;   // StructInst / (EnumInst, variant).

    int64_t PadAlign(TypeExpr *t);
    Layout LayoutFields(const vector<Field> &fields, const vector<TypeExpr *> &ftypes);
    const Layout &StructLayout(StructInst *si);
    const Layout &VariantLayout(EnumInst *ei, int vi);
    int64_t FixedSize(TypeExpr *t);

    TypeExpr *FoTailArr(TypeExpr *t);
    // Prefix before the innermost resizable tail in its byte image.
    int64_t FoBytesPrefix(TypeExpr *t);
    bool IsFrameObj(TypeExpr *t) { return t->kind == TY_STRUCT && SI(t)->frameobj; }
};

inline bool ValueLayout::TEq(TypeExpr *a, TypeExpr *b) {
    if (a == b) return true;
    if (a->kind != b->kind) return false;
    switch (a->kind) {
        case TY_INT:  return a->intstorage == b->intstorage;
        case TY_FLT:  return a->fltstorage == b->fltstorage;
        case TY_BOOL: case TY_VOID: case TY_FN: return true;
        case TY_STRUCT: return SI(a) == SI(b);
        case TY_ENUM:   return EIOf(a) == EIOf(b) && a->enu->varmode == b->enu->varmode;
        case TY_ARRAY: {
            auto &x = *a->arr, &y = *b->arr;
            if (x.akind != y.akind || !TEq(x.sub, y.sub)) return false;
            switch (x.akind) {
                case A_FIXED: case A_LIMITED: return ArrSize(a->arr) == ArrSize(b->arr);
                case A_VAR:     return LenStore(a->arr) == LenStore(b->arr);
                default:        return true;
            }
        }
        case TY_SLICE: return TEq(a->sub, b->sub);
        case TY_REF:
            return TEq(a->ref->sub, b->ref->sub) && a->ref->optional == b->ref->optional &&
                   a->ref->lenstorage == b->ref->lenstorage;
        case TY_VARIANT:
            return a->var->variant == b->var->variant && TEq(a->var->adt, b->var->adt);
        default: assert(false); return false;
    }
}

// Instantiations: the typechecker filled the per-TypeExpr caches for every
// type it touched; fall back to an argument-equality search for clones.
inline StructInst *ValueLayout::SI(TypeExpr *t) {
    assert(t->kind == TY_STRUCT);
    if (t->struc->inst) return t->struc->inst;
    for (auto inst : t->struc->st->insts) {
        if (inst->args.size() != t->struc->args.size()) continue;
        auto ok = true;
        for (size_t i = 0; i < inst->args.size(); i++)
            ok &= TEq(inst->args[i], t->struc->args[i]);
        if (ok) return t->struc->inst = inst;
    }
    assert(false);
    return nullptr;
}

inline EnumInst *ValueLayout::EIOf(TypeExpr *t) {
    assert(t->kind == TY_ENUM);
    if (t->enu->inst) return t->enu->inst;
    for (auto inst : t->enu->en->insts) {
        if (inst->args.size() != t->enu->args.size()) continue;
        auto ok = true;
        for (size_t i = 0; i < inst->args.size(); i++)
            ok &= TEq(inst->args[i], t->enu->args[i]);
        if (ok) return t->enu->inst = inst;
    }
    assert(false);
    return nullptr;
}

inline EnumInst *ValueLayout::EIVar(TypeExpr *t) {   // For TY_VARIANT.
    assert(t->kind == TY_VARIANT);
    return EIOf(t->var->adt);
}

inline span<const FieldRun> ValueLayout::FieldRuns(TypeExpr *t) {
    switch (t->kind) {
        case TY_STRUCT: return RunsOf(SI(t));
        case TY_ENUM: return RunsOf(EIOf(t));
        case TY_VARIANT: {
            auto ei = EIVar(t);
            return RunsOf(ei, ei->en->VariantIndex(t->var->variant));
        }
        default: return {};
    }
}

inline SizeClass ValueLayout::Cls(TypeExpr *t) {
    switch (t->kind) {
        case TY_INT: return t->intstorage == IS_VARINT ? SC_VARIABLE : SC_FIXED;
        case TY_REF: return t->ref->lenstorage == IS_VARINT ? SC_VARIABLE : SC_FIXED;
        case TY_STRUCT: return SI(t)->sclass;
        case TY_ENUM: return t->enu->varmode ? EIOf(t)->varclass : SC_FIXED;
        case TY_ARRAY:
            switch (t->arr->akind) {
                case A_FIXED:   return SC_FIXED;
                case A_VAR:     return SC_VARIABLE;
                case A_LIMITED: return ArrSize(t->arr) >= 0 ? SC_FIXED : SC_VARIABLE;
                default:        return SC_RESIZABLE;
            }
        case TY_VARIANT: {
            auto c = SC_FIXED;
            EachField(t, [&](TypeExpr *ft) { c = std::max(c, Cls(ft)); });
            return c;
        }
        default: return SC_FIXED;
    }
}

inline TypeExpr *ValueLayout::FoTailArr(TypeExpr *t) {
    auto si = SI(t);
    auto ft = si->ftypes[LastRealField(si->st->fields)];
    return IsFrameObj(ft) ? FoTailArr(ft) : ft;
}

inline int64_t ValueLayout::FoBytesPrefix(TypeExpr *t) {
    auto si = SI(t);
    int64_t n = 0;
    for (size_t i = 0; i < si->st->fields.size(); i++) {
        auto &f = si->st->fields[i];
        if (f.ispad) { n += f.padsize > 0 ? f.padsize : 0; continue; }
        auto ft = si->ftypes[i];
        if (IsResz(ft)) return n + (IsFrameObj(ft) ? FoBytesPrefix(ft) : 0);
        n += FixedSize(ft);
    }
    assert(false);   // A frame object ends in its tail.
    return n;
}

// The stored length-field type of an array (A_VAR: declared or u32
// default; A_LIMITED with static capacity: smallest fitting type).
inline IntStorage ValueLayout::LenStore(TypeArray *a) {
    switch (a->akind) {
        case A_VAR:
            return a->lenstorage < 0 ? IS_U32 : (IntStorage)a->lenstorage;
        case A_LIMITED: {
            auto k = ArrSize(a);
            assert(k >= 0);
            return k <= 255 ? IS_U8 : k <= 65535 ? IS_U16 :
                   k <= (int64_t)UINT32_MAX ? IS_U32 : IS_U64;
        }
        default: assert(false); return IS_U32;
    }
}

// StructInst / (EnumInst, variant).

// The alignment `pad` (bare form) gives the next field: its scalar width.
inline int64_t ValueLayout::PadAlign(TypeExpr *t) {
    switch (t->kind) {
        case TY_INT: return t->intstorage == IS_VARINT ? 1 : IntSize(t->intstorage);
        case TY_FLT: return t->fltstorage == FS_F32 ? 4 : 8;
        case TY_REF: return t->ref->lenstorage >= 0 ?
                            (t->ref->lenstorage == IS_VARINT ? 1
                                                             : IntSize((IntStorage)t->ref->lenstorage))
                            : 8;
        case TY_SLICE: return 8;
        default: return 1;
    }
}

inline ValueLayout::Layout ValueLayout::LayoutFields(const vector<Field> &fields,
                                             const vector<TypeExpr *> &ftypes) {
    Layout lo;
    int64_t off = 0;
    for (size_t i = 0; i < fields.size(); i++) {
        auto &f = fields[i];
        if (f.ispad) {
            lo.offs.push_back(off);
            if (f.padsize >= 0) {
                off += f.padsize;
            } else {
                // Bare pad: align the next real field to its own size.
                TypeExpr *nt = nullptr;
                for (auto j = i + 1; j < fields.size(); j++)
                    if (!fields[j].ispad) { nt = ftypes[j]; break; }
                auto a = nt ? PadAlign(nt) : 1;
                off = (off + a - 1) / a * a;
            }
            continue;
        }
        lo.offs.push_back(off);
        off += FixedSize(ftypes[i]);
    }
    lo.size = off;
    return lo;
}

inline const ValueLayout::Layout &ValueLayout::StructLayout(StructInst *si) {
    auto key = pair<const void *, int>(si, -1);
    auto it = layouts.find(key);
    if (it != layouts.end()) return it->second;
    return layouts[key] = LayoutFields(si->st->fields, si->ftypes);
}

inline const ValueLayout::Layout &ValueLayout::VariantLayout(EnumInst *ei, int vi) {
    auto key = pair<const void *, int>(ei, vi);
    auto it = layouts.find(key);
    if (it != layouts.end()) return it->second;
    return layouts[key] = LayoutFields(ei->en->variants[vi].fields, ei->vftypes[vi]);
}

inline int64_t ValueLayout::FixedSize(TypeExpr *t) {
    switch (t->kind) {
        case TY_INT:  assert(t->intstorage != IS_VARINT); return IntSize(t->intstorage);
        case TY_FLT:  return t->fltstorage == FS_F32 ? 4 : 8;
        case TY_BOOL: return 1;
        case TY_REF:
            if (t->ref->lenstorage >= 0) {
                assert(t->ref->lenstorage != IS_VARINT);
                return IntSize((IntStorage)t->ref->lenstorage);
            }
            return IsResz(t->ref->sub) ? 16 : 8;
        case TY_SLICE: return 16;
        case TY_STRUCT: {
            // An empty struct takes the one byte C gives it.
            auto sz = StructLayout(SI(t)).size;
            return sz ? sz : 1;
        }
        case TY_ENUM: {
            assert(!t->enu->varmode);
            auto ei = EIOf(t);
            int64_t maxp = 0;
            for (size_t vi = 0; vi < ei->en->variants.size(); vi++)
                maxp = std::max(maxp, VariantLayout(ei, (int)vi).size);
            return TagSize(ei->en) + maxp;
        }
        case TY_VARIANT: {
            auto ei = EIVar(t);
            return VariantLayout(ei, ei->en->VariantIndex(t->var->variant)).size;
        }
        case TY_ARRAY: {
            auto &a = *t->arr;
            switch (a.akind) {
                case A_FIXED:   return ArrSize(t->arr) * FixedSize(a.sub);
                case A_LIMITED: return IntSize(LenStore(t->arr)) +
                                       ArrSize(t->arr) * FixedSize(a.sub);
                default: assert(false); return 0;
            }
        }
        default: assert(false); return 0;
    }
}

}  // namespace goose
