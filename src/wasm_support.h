// Wasm admission policy. Layout numbers remain owned by ValueLayout.
#pragma once

namespace goose {

struct WasmValueSupport {
    ValueLayout &layout;
    ValueLayout::FixedSizes sizes;
    unordered_set<TypeExpr *> validated;

    explicit WasmValueSupport(ValueLayout &l) : layout(l) {}
    static bool Nominal(TypeExpr *t) {
        return t && (t->kind == TY_STRUCT || t->kind == TY_ENUM || t->kind == TY_VARIANT);
    }
    bool InlineArray(TypeExpr *t) const {
        return t->kind == TY_ARRAY && (t->arr->akind == A_FIXED ||
               (t->arr->akind == A_LIMITED && t->arr->size >= 0));
    }
    bool ScalarElement(TypeExpr *t) {
        return t->kind == TY_BOOL || t->kind == TY_INT || t->kind == TY_FLT ||
               (t->kind == TY_REF && !layout.IsResz(t->ref->sub));
    }
    bool DataNominalArray(TypeExpr *t) {
        return t->kind == TY_ARRAY && t->arr->akind == A_VAR &&
               layout.LenStore(t->arr) != IS_VARINT && Nominal(t->arr->sub);
    }
    const char *Check(TypeExpr *root) {
        if (validated.count(root)) return nullptr;
        vector<TypeExpr *> work {root};
        unordered_set<TypeExpr *> seen;
        auto fields = [&](const vector<TypeExpr *> &types) -> const char * {
            for (auto field : types) if (field) {
                if (field->kind == TY_ARRAY && !InlineArray(field))
                    return "nonfixed struct fields need the pending destination lowering";
                if (field->kind == TY_REF && layout.IsResz(field->ref->sub))
                    return "compound owner-reference fields need the pending destination lowering";
                work.push_back(field);
            }
            return nullptr;
        };
        for (size_t i = 0; i < work.size(); i++) {
            auto t = work[i];
            if (validated.count(t) || !seen.insert(t).second) continue;
            switch (t->kind) {
                case TY_VOID: case TY_BOOL: case TY_FLT: break;
                case TY_INT:
                    if (t->intstorage == IS_VARINT) return "varint value storage needs the pending layout lowering";
                    if (t->ix) return "index and bound types are not implemented";
                    break;
                case TY_REF:
                    if (t->ref->lenstorage >= 0 || t->ref->pool)
                        return "relative references need the pending layout lowering";
                    work.push_back(t->ref->sub);
                    break;
                case TY_ARRAY:
                    if (!ScalarElement(t->arr->sub) &&
                        !(InlineArray(t) && Nominal(t->arr->sub)) && !DataNominalArray(t))
                        return "compound array elements need the pending layout lowering";
                    work.push_back(t->arr->sub);
                    break;
                case TY_STRUCT: {
                    auto si = layout.SI(t);
                    if (!layout.IsFix(t) || si->st->isroot || si->frameobj)
                        return "nonfixed or root structs need the pending layout lowering";
                    if (auto reason = fields(si->ftypes)) return reason;
                    break;
                }
                case TY_ENUM: {
                    auto ei = layout.EIOf(t);
                    if (t->enu->varmode || !ei->allfixed)
                        return "nonfixed enums need the pending layout lowering";
                    if (ei->en->variants.empty() || ei->en->variants.size() > 65536)
                        return "fixed enum exceeds its u16 tag range";
                    for (auto &types : ei->vftypes)
                        if (auto reason = fields(types)) return reason;
                    break;
                }
                case TY_VARIANT: {
                    if (!layout.IsFix(t)) return "nonfixed variants need the pending layout lowering";
                    auto ei = layout.EIVar(t);
                    auto vi = ei->en->VariantIndex(t->var->variant);
                    if (vi < 0 || (size_t)vi >= ei->vftypes.size()) return "missing checked variant layout";
                    if (auto reason = fields(ei->vftypes[vi])) return reason;
                    break;
                }
                default: return "this fixed field layout needs the pending layout lowering";
            }
        }
        // No provisional success escapes a recursive reference cycle.
        for (auto t : seen) if (Nominal(t) || InlineArray(t)) {
            uint64_t bytes;
            if (!layout.TryFixedSize(t, UINT32_MAX, bytes, sizes))
                return "fixed aggregate layout exceeds memory32";
            if (InlineArray(t) && Nominal(t->arr->sub) && !sizes.at(t->arr->sub))
                return "zero-stride aggregate elements need the pending layout lowering";
        }
        for (auto t : seen) if (DataNominalArray(t)) {
            uint64_t bytes;
            if (!layout.TryFixedSize(t->arr->sub, UINT32_MAX, bytes, sizes))
                return "fixed aggregate layout exceeds memory32";
            if (!bytes) return "zero-stride aggregate elements need the pending layout lowering";
        }
        validated.insert(seen.begin(), seen.end());
        return nullptr;
    }
};

}  // namespace goose
