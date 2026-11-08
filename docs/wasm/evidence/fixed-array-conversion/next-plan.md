# Next compilation gap

Ten native-valid O0 cases already fail Wasm compilation with the saved
compound-math candidate. Five receiver layouts are tested with both addition
and negation: i64[], i64[>..], i64[>..<], i64[..], and i64[varint]. Raw parent01
records, source files, compiler commands, stdout/stderr and exits are preserved.
The exact source of that compiler will be committed c7008561, SHA in the
compound-math compiler identity. Do not rerun these passed parent cases.

Current blocker: InitArray handles fixed arithmetic only for inline receivers.
The contextual exprtype of a math result is nonfixed, so InitArrayCopy passes
its exact check but ResolveArray/Gen rejects the array temporary. Native MathType
recovers intrinsic fixed operands before adapting its result.

A local array-initialization adapter can recover intrinsic fixed type from
unary minus or binary +/-/*///% operands (strip refs; choose array operand for
scalar broadcast). Do not globally change ActualType: static limited arithmetic
assignments rely on current contextual types. Source calls/idents/fields with
already-known actual fixed-array type could share this path, but first add
native-first coverage if widening admission beyond arithmetic.

Use WithFixedValue with the natural fixed array type. The root contextual
exprtype can remain nonfixed, so construct arithmetic directly through
ConstructFixedBinary or NegateFixedInto/FixedMathDestination rather than relying
on ConstructFixed's contextual FixedBinary predicate. General fixed-call or
copy producers can use ConstructFixed if actually admitted with coverage.

The receiving declaration scope must be captured BEFORE opening the temporary
scope. All old data allocation helpers append restores to scopes.back(); doing
that inside the temporary consumer releases the receiver too soon. Register its
restore at the captured declaration scope, not the temporary scope. Globals do
not get a scoped data restore. Keep temporary source live through the copy.

Use ArrayAllocationMemory/storage.Memory/StackIndex for actual receiver namespace,
including hidden runtime bases. Reserve payload bytes plus DataPrefix(array,count)
when DataArray; growable headers stay in Memory 0. Write runtime-limited capacity
and length through InitArrayCount; growable pointer/length through
FrameArrayOwner and field helpers. Copy fixed payload once with CopyBytes.
Prefix is absent from source fixed payload. Preserve fixed/static-limited old
paths. Existing compound-array-element and unrelated layout guards stay.

Check payload+prefix overflow and stored-prefix limits. Investigate native-valid
narrow-prefix overflow behavior before choosing compile rejection versus runtime
failure. Zero-count arithmetic still evaluates both operands. Runtime-limited
cap and len should both start at count. Varint prefix transitions need tests.

Focused coverage should include all operators/scalar orders, effects, empty/large
counts, padding, data-memory owner images/live tops, globals, multiple call bases,
copy/root independence, mutation controls and early exits. No timing, performance
gates, leases or resource handoffs. Current owner directive is correctness only.
