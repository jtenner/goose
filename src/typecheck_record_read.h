// Checked, eager little-endian snapshots of flat integer wire records.
#pragma once

namespace goose {

inline Val TypeCheck::CheckRecordRead(Call *c, vector<Node *> &args) {
    if (c->tyargs.size() != 1)
        Error(c, "read_record_le needs exactly one explicit type argument");
    auto t = Subst(c->tyargs[0]);
    // Reject qualifiers before ValueType can discard them. Aliases have
    // already resolved to their underlying type through ordinary substitution.
    if (t->cq || t->kind != TY_STRUCT || IsWord(t))
        Error(c, "read_record_le requires an unqualified ordinary struct");
    auto st = t->struc->st;
    if (st->isroot)
        Error(c, "read_record_le does not support root structs");
    if (!st->generics.empty() || !t->struc->args.empty())
        Error(c, "read_record_le does not support generic structs");

    // Selection preserves the original field tree. Even an inactive or
    // empty conditional arm is not a stable wire schema in this version.
    for (auto &f : st->declfields)
        if (f.condition)
            Error(f.line, "read_record_le does not support conditional fields");
    for (auto &f : st->fields) {
        if (f.condition)
            Error(f.line, "read_record_le does not support conditional fields");
        if (f.ispad)
            Error(f.line, "read_record_le does not support padding");
        if (f.defaultval)
            Error(f.line, "read_record_le does not support field defaults");
        if (f.isconst)
            Error(f.line, "read_record_le requires writable fields");
    }
    if (st->fields.empty())
        Error(c, "read_record_le requires a nonempty struct");

    ValidateType(t, c->line, VT_LOCAL);
    auto si = GetStructInst(t);
    int64_t extent = 0;
    // The compiler uses signed i64 object sizes. Also respect the host's
    // addressable object limit; no layout computation may wrap that limit.
    auto limit = std::min(uint64_t(INT64_MAX), uint64_t(SIZE_MAX >> 1));
    for (size_t i = 0; i < st->fields.size(); ++i) {
        auto &f = st->fields[i];
        auto ft = si->ftypes[i];
        if (ft->cq)
            Error(f.line, "read_record_le requires unqualified writable integer fields");
        if (!IsIntT(ft) || ft->ix || ft->intstorage == IS_VARINT)
            Error(f.line, cat("read_record_le field ", f.name,
                              " must be u8/u16/u32/u64 or i8/i16/i32/i64"));
        auto width = IntBits(ft->intstorage) / 8;
        if (uint64_t(extent) > limit || uint64_t(width) > limit - uint64_t(extent))
            Error(f.line, "read_record_le record extent exceeds the object-size limit");
        extent += width;
    }
    assert(extent > 0);

    // These are ordinary argument adaptations, in source order. In
    // particular a safe byte array may adapt to the const byte slice;
    // handles, pointers and shared capabilities cannot do so.
    CheckArg(args[0], ast.inttypes[IS_I64]);
    CheckArg(args[1], cu8slice);
    c->qtype = t;
    c->rettypes.push_back(t);
    c->rettypes.push_back(ast.booltype);

    // Fresh fixed-value provenance: the input slice's roots never escape.
    Val value;
    value.type = t;
    value.Set(TempRoot(), false);
    Val ok;
    ok.type = ast.booltype;
    lastcallrets = {value, ok};
    return value;
}

} // namespace goose
