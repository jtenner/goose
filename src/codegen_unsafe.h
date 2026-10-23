// Explicitly unsafe native pointer intrinsics. No shared capability or runtime
// registry is involved. These checks cover numerical addresses only: valid
// provenance, object bounds, lifetime and synchronization belong to the caller.
#pragma once

namespace goose {

inline void CodeGen::EmitUnsafePtrType() {
    if (!used.insert("gs_unsafe_ptr").second) return;
    // Goose currently lays out ordinary pointers as 8-byte fields too. Reject
    // a different target rather than silently mis-layout a packed native value.
    tdecls +=
        "/* UnsafePtr: raw object pointer ABI; never a safe shared capability. */\n"
        "#if !defined(UINTPTR_MAX) || UINTPTR_MAX != UINT64_MAX\n"
        "#error \"UnsafePtr requires a 64-bit uintptr_t target; unsupported pointer width\"\n"
        "#endif\n"
        "typedef char gs_unsafe_pointer_width_check[(sizeof(void *) == 8 && "
        "sizeof(uintptr_t) == 8) ? 1 : -1];\n"
        "typedef void *gs_unsafe_ptr;\n\n";
}

inline vector<string> CodeGen::EmitUnsafeBuiltin(Call *c) {
    EmitUnsafePtrType();
    auto ln = c->line;
    vector<string> a;
    // Snapshot every argument once, in Goose evaluation order, before checks.
    for (auto n : c->ArgNodes()) a.push_back(Snapshot(n->exprtype, GenPure(n)));
    auto fail = [&](const string &condition, const string &message) {
        L("if (", condition, ") gs_abort_msg((const uint8_t *)", CStr(message), ", ",
          message.size(), ", ", LocArgs(ln), ");");
    };
    auto out = T();
    switch (c->builtin) {
        case B_UNSAFE_PTR_FROM_HANDLE:
            fail(cat(a[0], " > UINTPTR_MAX"), "unsafe pointer handle exceeds target width");
            L("gs_unsafe_ptr ", out, " = ", a[0], " == 0 ? NULL : (void *)(uintptr_t)", a[0], ";");
            return {out};
        case B_UNSAFE_HANDLE_FROM_PTR:
            L("uint64_t ", out, " = ", a[0], " == NULL ? 0 : (uint64_t)(uintptr_t)", a[0], ";");
            return {out};
        case B_UNSAFE_PTR_ADD: {
            fail(cat(a[0], " == NULL"), "unsafe pointer is null");
            auto address = T(), magnitude = T();
            L("uintptr_t ", address, " = (uintptr_t)", a[0], ";");
            // -(INT64_MIN) is never evaluated. Work in the integer address
            // domain, avoiding C pointer arithmetic before the caller's
            // same-object/bounds obligation at subsequent use.
            L("uint64_t ", magnitude, " = ", a[1], " < 0 ? (uint64_t)(-(", a[1],
              " + 1)) + UINT64_C(1) : (uint64_t)", a[1], ";");
            fail(cat(a[1], " < 0 ? ", magnitude, " > ", address, " : ", magnitude,
                     " > UINTPTR_MAX - ", address), "unsafe pointer address overflow");
            L("uintptr_t ", out, "_address = ", a[1], " < 0 ? ", address,
              " - (uintptr_t)", magnitude, " : ", address, " + (uintptr_t)", magnitude, ";");
            L("gs_unsafe_ptr ", out, " = ", out, "_address == 0 ? NULL : (void *)", out, "_address;");
            return {out};
        }
        case B_UNSAFE_LOAD: case B_UNSAFE_STORE: {
            auto size = IntSize(c->qtype->intstorage);
            auto utype = cat("uint", size * 8, "_t");
            auto bytes = T(), bits = T(), index = T();
            auto big = a[c->builtin == B_UNSAFE_LOAD ? 1 : 2];
            fail(cat(a[0], " == NULL"), "unsafe pointer is null");
            fail(cat(size - 1, " > UINTPTR_MAX - (uintptr_t)", a[0]),
                 "unsafe pointer address overflow");
            L("uint8_t ", bytes, "[", size, "];");
            if (c->builtin == B_UNSAFE_LOAD) {
                L("memcpy(", bytes, ", ", a[0], ", ", size, ");");
                L(utype, " ", bits, " = 0;");
                L("for (unsigned ", index, " = 0; ", index, " < ", size, "; ++", index, ")");
                L("    ", bits, " |= (", utype, ")((uint64_t)", bytes, "[", big, " ? ",
                  size - 1, " - ", index, " : ", index, "] << (8 * ", index, "));");
                L(CT(c->qtype), " ", out, ";");
                // Signed intN_t has no padding; copy the bits rather than rely
                // on implementation-defined unsigned-to-signed conversion.
                L("memcpy(&", out, ", &", bits, ", ", size, ");");
                return {out};
            }
            L(utype, " ", bits, " = (", utype, ")", a[1], ";");
            L("for (unsigned ", index, " = 0; ", index, " < ", size, "; ++", index, ")");
            L("    ", bytes, "[", big, " ? ", size - 1, " - ", index, " : ", index,
              "] = (uint8_t)((uint64_t)", bits, " >> (8 * ", index, "));");
            L("memcpy(", a[0], ", ", bytes, ", ", size, ");");
            return {};
        }
        default: assert(false); return {};
    }
}

}  // namespace goose
