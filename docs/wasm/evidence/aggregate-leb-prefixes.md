# Fixed aggregates with unsigned LEB128 counts

Fixed structs, enums and standalone variants now use variable data arrays with
canonical unsigned LEB128 count prefixes. The parent is
`c727452fdf7c585e277b8bb3e19f2a91d4a19836`.
The tested Release compiler SHA256 is
`9f833fad0aa896cec2b77e00cfd4338bf807eefb7f2cb34a5fea10a298fa14a4`.
This work is correctness only.

## Narrow implementation

`DataNominalArray` now admits the existing unsigned LEB prefix. The existing
fixed-layout, positive-stride and memory32 checks still apply to each element.
Fresh literal and fill reservations use `DataPrefix(array, literalCount)`.
This derives the canonical width from the actual count, including three- and
five-byte prefixes, instead of using the fixed-prefix layout query.

Exact stored LEB copies use the existing `InitArrayCopy` path. It captures the
source count and decoded prefix width before checking the payload product and
whole-byte sum. It then reserves the receiver and copies the complete prefix
and active payload. Packed source and receiver memory identities and ordered
cleanup retain their existing behavior. The fixed-prefix dynamic reservation
helper explicitly rejects a LEB request without a captured source prefix.

Existing fixed/limited-source adapters, stored-prefix conversion, borrowed
reference ABI, indexing and copied iteration already use decoded LEB widths.
No new descriptor field, table, IR form, runtime representation or shared
interface is added. The compiler changes two private Wasm headers. Aggregate
array equality remains an explicit target diagnostic.

## Failing-first and differential evidence

All 33 families pass native execution on the parent and fail its precise
compound-element Wasm admission guard. They cover empty and explicit literals,
fills, stored copies, prefix conversions, fixed and limited sources, borrowed
calls, reference fields in data elements, globals, copied iteration, enums,
variants, ordinary references, defaults and structured initializer exits.
Active count tests include 127, 128, 16,383 and 16,384.

Two further cases within those 33 families use counts requiring four- and
five-byte prefixes. A non-inlined function receives a false runtime flag, so
its large-fill body does not execute. Native and Wasm executions check that
path without allocating the large payload. These cases prove admission and
reservation-code construction, not execution of the large prefix payloads.

The candidate executes all 33 families at O0/O2 under native code, Node and
Wasmtime, with completed Memory 0/data-owner checks. Assertion-enabled compiler
output must match the same 66 Release modules and pass Node checks.

## Complete images and fault controls

The new helper unit has 126 checks. Fill models derive canonical bytes
independently and compare complete Memory 0 and data images at the start,
during value evaluation, after copying and after cleanup. Prefix transitions
and empty fills use poisoned free bytes and distinct boundary sentinels.

Borrowed exact copies run twice, with a caller owner live on the second call.
The receiver moves from data memory 2 to memory 3 while preserving the source
in memory 1 and the caller's poisoned free bytes. Empty copies must still copy
the one-byte prefix. Nonempty copies must include the decoded two-byte prefix.
Every source, caller and receiver top is checked at its completion signal.

Validated damaged modules omit evaluation, shorten or extend copies, alter
stored prefix bytes, shift payload offsets, change packed memory identities,
omit restoration or corrupt Memory 0. A decoded-width control forces width
one for a two-byte stored prefix and must fail the receiving-top assertion.
Each control requires its specific state or complete-image failure.

The models compare full Buffers with `Buffer.equals` and a concise assertion
message. The first large short-copy control hit the test timeout while using
the verbose Buffer assertion. Its failure is preserved. The unchanged mutant
then failed the intended full-image assertion with the concise observer, and
the complete image unit was rerun. No byte comparison was removed, no timeout
limit was raised, and no compiler change was made for that observer issue.

A separate eight-check unit corrupts the source count to exercise payload
product and decoded-prefix sum overflow. The product case wraps multiplication
modulo 2^64 to one if its guard is bypassed. The sum case has a valid product
but overflows memory32 after adding the five-byte prefix. Healthy modules must
fail with the specific size error before receiver allocation and preserve all
complete images. A bypassed guard must reach the forbidden copy checkpoint.
These are malformed-header tests, not native-valid source values. They do not
claim terminal-trap cleanup or reentry support.

## Retained guards and setup limits

A native-valid equality function takes two separate borrowed arrays and must
retain the exact aggregate-array-equality rejection at O0/O2. The previous LEB
admission guard is replaced with a native-valid growable-aggregate rejection.
The C++ layout unit checks all five prefix kinds and the positive-stride guard.

The first copied-iteration sketch used an invalid binder spelling. Its failure
remains; the ordinary copied binder and its real loop pass the corrected
parent unit. An attempted zero-stride source used a standalone variant without
fields. The shared frontend rejects that element type before either target.
That check is retained as frontend rejection coverage. Synthetic C++ layout
checks cover the backend's zero-stride policy; no native runtime coverage is
claimed for an input the frontend rejects.

## Full-suite continuation

The first integrated run completed 6,243 main checks, including all core units
and the verified fixture phase. It then stopped at an older `data-varint`
admission entry that still expected rejection. That native-valid program
passes a nested fixed-array field to a recursive reader and expects 22.
It now passes native, Node, Wasmtime and completed-owner checks at O0/O2 in a
dedicated unit. Its legacy helper entry is positive; all other entry policies
remain unchanged.

The failed run, original helper, complete input hashes and control-flow state
remain. A new continuation verifies the completed prefix, all module hashes
and the single changed helper before executing that helper and every later
check afresh. The first continuation stopped before tests because its static
name check did not account for nested Python function and argument bindings.
The corrected setup is a separate attempt. No failed run is called a full pass.

## Final record and costs

All 7,991 correctness checks passed across the verified completed prefix and
the final remaining-helper phase. All 1,978 old fixture modules are
byte-identical to executed parent modules. All 66 new assertion-enabled
modules match Release. All 52 exact output and diagnostic comparisons pass.
The final verifier checks all 85 compiler source files and 6,125 test/script
inputs.

The [final validation record](aggregate-leb-prefixes/final-validation.json)
records selected results and frozen identities. Raw evidence remains under
`/tmp/goose-wasm-aggregate-leb-20261109`.

This reuses existing prefix and copy machinery. Receiving bytes and copy work
grow with active payload size, with the actual canonical count prefix. Fills
retain one existing element snapshot. No timing, profiling, allocation-total,
compiler-cost or physical-memory measurement is part of this work.

Aggregate equality, runtime/growable aggregate elements, nonfixed fields and
value transport, signed-varint elements, slices, relative references, pools,
native adapters and workers remain separate. The full backend is incomplete;
Stage F scope remains an owner question.
