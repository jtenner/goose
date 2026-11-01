// Packed word scalar extraction, construction and checked whole-word updates.
#pragma once
namespace goose {
inline string CodeGen::WordMask(int bits) {
    auto mask = bits == 64 ? UINT64_MAX : (uint64_t(1) << bits) - 1;
    return cat(mask, "ULL");
}

inline string CodeGen::WordRead(Dot *d) {
    auto owner = WordObject(d);
    auto &f = owner->struc->st->fields[d->fieldidx];
    auto raw = GenPure(d->obj);
    if (d->obj->exprtype->kind == TY_REF) raw = PointeeLv(raw, owner);
    auto extract = cat("((", raw, " >> ", f.bitoffset, ") & ", WordMask(f.bits), ")");
    if (d->exprtype->kind != TY_ENUM) return cat("(", CT(d->exprtype), ")", extract);
    auto count = d->exprtype->enu->en->variants.size();
    auto tag = T(); L("uint64_t ", tag, " = (uint64_t)", extract, ";");
    if (f.bits >= 64 || count != (uint64_t(1) << f.bits)) {
        auto msg = cat("invalid enum tag in packed word field ", owner->struc->st->name, ".", f.name);
        L("if (", tag, " >= ", count, ") gs_abort_msg((const uint8_t *)", CStr(msg), ", ", msg.size(), ", ", LocArgs(d->line), ");");
    }
    auto value = T(); FixedLocal(d->exprtype, value);
    L(value, ".tag = ", tag, ";");
    return value;
}

inline string CodeGen::WordInput(Node *n, TypeExpr *owner, const Field &f) {
    auto value = Snapshot(n->exprtype, GenPure(n));
    if (f.bitwidth.empty()) {
        if (n->exprtype->kind == TY_ENUM) return cat(value, ".tag");
        return value;
    }
    auto nt = n->exprtype;
    if (!IsIntT(nt) || !IsUnsigned(nt->intstorage) || IntBits(nt->intstorage) > f.bits) {
        auto msg = cat("packed word field ", owner->struc->st->name, ".", f.name,
                       " value is outside range 0..", (f.bits == 64 ? UINT64_MAX : (uint64_t(1) << f.bits) - 1));
        L("if (", value, " > ", WordMask(f.bits), ") gs_abort_msg((const uint8_t *)", CStr(msg), ", ", msg.size(), ", ", LocArgs(n->line), ");");
    }
    return value;
}

inline void CodeGen::WordConstruct(StructLit *sl, const string &destination) {
    auto owner = sl->exprtype;
    auto ct = CT(owner);
    // Do not publish a partially constructed word to an existing destination.
    auto result = T(); L(ct, " ", result, " = 0;");
    for (size_t i = 0; i < sl->sinst->st->fields.size(); ++i) {
        auto &f = sl->sinst->st->fields[i];
        if (f.ispad) continue;
        auto value = WordInput(sl->InitFor((int)i), owner, f);
        // u8/u16 are promoted to unsigned 32 bits before shifting.
        auto calc = "uint64_t";
        L(result, " |= (", ct, ")(((", calc, ")(", value, ") & ", WordMask(f.bits), ") << ", f.bitoffset, ");");
    }
    L(destination, " = ", result, ";");
}

inline void CodeGen::WordWrite(Dot *d, Node *rhs, TType op, Line line) {
    auto owner = WordObject(d);
    auto &f = owner->struc->st->fields[d->fieldidx];
    auto loc = GenLocNow(d->obj);
    if (loc.t->kind == TY_REF) DerefLoc(loc);
    // Only an indirect/unstable whole-word location needs pinning. A local
    // word stays a C scalar name, including when the RHS contains calls.
    if (loc.viaref || !StableDest(d->obj)) PinLoc(loc);
    auto ct = CT(owner);
    auto calc = "uint64_t";
    auto mask = WordMask(f.bits);
    string old;
    if (op != T_ASSIGN) {
        old = T();
        L(calc, " ", old, " = (", calc, ")((", LoadLoc(loc, owner, line), " >> ", f.bitoffset, ") & ", mask, ");");
    }
    auto value = rhs ? (op == T_ASSIGN ? WordInput(rhs, owner, f) : Snapshot(rhs->exprtype, GenPure(rhs))) : "1";
    if (op != T_ASSIGN) {
        auto fail = [&](const string &condition) {
            auto msg = cat("packed word field ", owner->struc->st->name, ".", f.name, " arithmetic is outside its range");
            L("if (", condition, ") gs_abort_msg((const uint8_t *)", CStr(msg), ", ", msg.size(), ", ", LocArgs(line), ");");
        };
        string operation;
        switch (op) {
            case T_PLUSEQ: case T_INC:
                fail(cat(value, " > ", mask, " - ", old)); operation = "+"; break;
            case T_MINUSEQ: case T_DEC:
                fail(cat(value, " > ", old)); operation = "-"; break;
            case T_MULEQ:
                fail(cat(old, " && ", value, " > ", mask, " / ", old)); operation = "*"; break;
            case T_DIVEQ: case T_MODEQ:
                fail(cat(value, " == 0")); operation = op == T_DIVEQ ? "/" : "%"; break;
            case T_ANDEQ: operation = "&"; break;
            case T_OREQ: operation = "|"; break;
            case T_XOREQ: operation = "^"; break;
            case T_SHLEQ: case T_SHREQ: {
                auto shift = T();
                L("unsigned ", shift, " = (unsigned)(", value, ") & ", IntBits(d->exprtype->intstorage) - 1, ";");
                value = shift;
                if (op == T_SHLEQ) fail(cat(old, " > (", mask, " >> ", shift, ")"));
                operation = op == T_SHLEQ ? "<<" : ">>";
                break;
            }
            default: Fail(line, "internal: unsupported packed word update");
        }
        auto result = T();
        // Keep the full unsigned carrier until after the field range check.
        auto resultct = "uint64_t";
        L(resultct, " ", result, " = (", resultct, ")", old, " ", operation, " (", resultct, ")(", value, ");");
        fail(cat(result, " > ", mask));
        value = result;
    }
    // Reload after the RHS: it may have changed a different field.
    auto before = LoadLoc(loc, owner, line);
    L(loc.s, " = (", ct, ")(((", calc, ")(", before, ") & ~((", calc, ")", mask, " << ", f.bitoffset,
      ")) | (((", calc, ")(", value, ") & ", mask, ") << ", f.bitoffset, "));");
}
} // namespace goose
