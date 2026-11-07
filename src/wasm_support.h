// Wasm admission policy. Layout numbers remain owned by ValueLayout.
#pragma once

namespace goose {

struct WasmValueSupport {
    ValueLayout &layout;
    ValueLayout::FixedSizes sizes;
    unordered_set<TypeExpr *> validated;

    explicit WasmValueSupport(ValueLayout &l) : layout(l) {}
    bool InlineArray(TypeExpr *t) const {
        return t->kind == TY_ARRAY && (t->arr->akind == A_FIXED ||
               (t->arr->akind == A_LIMITED && t->arr->size >= 0));
    }
    bool ScalarElement(TypeExpr *t) {
        return t->kind == TY_BOOL || t->kind == TY_INT || t->kind == TY_FLT ||
               (t->kind == TY_REF && !layout.IsResz(t->ref->sub));
    }
    const char *Check(TypeExpr *root) {
        if (validated.count(root)) return nullptr;
        vector<TypeExpr *> work {root};
        unordered_set<TypeExpr *> seen;
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
                    if (!ScalarElement(t->arr->sub)) return "compound array elements need the pending layout lowering";
                    work.push_back(t->arr->sub);
                    break;
                case TY_STRUCT: {
                    auto si = layout.SI(t);
                    if (!layout.IsFix(t) || si->st->isroot || si->frameobj)
                        return "nonfixed or root structs need the pending layout lowering";
                    for (auto field : si->ftypes) if (field) {
                        if (field->kind == TY_ARRAY && !InlineArray(field))
                            return "nonfixed struct fields need the pending layout lowering";
                        if (field->kind == TY_REF && layout.IsResz(field->ref->sub))
                            return "compound owner-reference fields need the pending layout lowering";
                        work.push_back(field);
                    }
                    break;
                }
                default: return "this fixed field layout needs the pending layout lowering";
            }
        }
        // No provisional success escapes a recursive reference cycle.
        for (auto t : seen) if (t->kind == TY_STRUCT || InlineArray(t)) {
            uint64_t bytes;
            if (!layout.TryFixedSize(t, UINT32_MAX, bytes, sizes))
                return "fixed aggregate layout exceeds memory32";
        }
        validated.insert(seen.begin(), seen.end());
        return nullptr;
    }
};

}  // namespace goose
