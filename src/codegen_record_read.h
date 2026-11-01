// One recoverable extent guard, then constant-offset unsigned byte assembly.
#pragma once

namespace goose {

inline vector<string> CodeGen::EmitRecordRead(Call *c, vector<Node *> &args) {
    auto t = c->qtype;
    auto si = SI(t);
    const auto &layout = StructLayout(si);

    // Force evaluation of the position before even computing the slice.
    // GenPure snapshots mutable scalar names as well as call results.
    auto at = GenPure(args[0]);
    auto source = GenPure(args[1]);

    // Always decode into fresh storage, regardless of the caller's eventual
    // destination. Its old bytes may themselves be the captured source.
    auto value = T();
    FixedLocal(t, value, "{0}");
    auto ok = T();
    auto start = T();
    auto length = T();
    L("uint8_t ", ok, " = 0;");
    L("uint64_t ", start, " = (uint64_t)(", at, ");");
    L("uint64_t ", length, " = (uint64_t)", source, ".len;");

    // Compute the sequential extent independently of the layout cache and
    // assert agreement before using that descriptor to store each member.
    int64_t extent = 0;
    for (size_t i = 0; i < si->ftypes.size(); ++i) {
        assert(layout.offs[i] == extent);
        extent += IntSize(si->ftypes[i]->intstorage);
    }
    assert(extent > 0 && layout.size == extent);

    L("if (", start, " <= ", length, " && ", extent,
      "ULL <= ", length, " - ", start, ") {");
    ind++;
    // No pointer arithmetic, source access or per-field check before this
    // guard. Byte loads support unaligned sources and either host endian.
    auto bytes = T();
    L("const uint8_t *", bytes, " = (const uint8_t *)", source, ".data + ", start, ";");
    Loc record;
    record.s = value;
    record.t = t;
    record.val = true;
    for (size_t i = 0; i < si->ftypes.size(); ++i) {
        auto ft = si->ftypes[i];
        auto storage = ft->intstorage;
        auto width = IntSize(storage);
        auto bits = T();
        string expression;
        for (int64_t b = 0; b < width; ++b) {
            if (b) expression += " | ";
            expression += cat("((uint64_t)", bytes, "[", layout.offs[i] + b,
                              "] << ", b * 8, ")");
        }
        L("uint64_t ", bits, " = ", expression, ";");
        string scalar;
        if (IsUnsigned(storage)) {
            scalar = cat("(", CT(ft), ")", bits);
        } else {
            // Avoid implementation-defined out-of-range unsigned-to-signed
            // conversion. For a negative encoding, ~bits (masked to the
            // field width) is representable; -1 minus it gives the exact
            // two's-complement value, including INT64_MIN without overflow.
            auto mask = width == 8 ? UINT64_MAX : (uint64_t(1) << (width * 8)) - 1;
            auto high = uint64_t(1) << (width * 8 - 1);
            scalar = cat("(", CT(ft), ")((", bits, " & ", high,
                         "ULL) ? (-1LL - (int64_t)(~", bits,
                         " & ", mask, "ULL)) : (int64_t)", bits, ")");
        }
        auto field = FieldLocAt(record, (int)i);
        L(field.s, " = ", scalar, ";");
    }
    L(ok, " = 1;");
    ind--;
    L("}");
    return {value, ok};
}

} // namespace goose
