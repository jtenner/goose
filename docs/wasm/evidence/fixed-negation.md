# Fixed numeric negation

Fixed numeric structs and arrays now support unary minus through checked
construction, assignment, arguments and results. The operand is resolved inside
its existing stored-value scope. Numeric fields are read from that source and
written to the checked fresh destination. Assignment still computes into its
protected temporary before committing a complete value. Negation does not mutate its operand; assignment then commits the result. No new runtime descriptor, compiler field or allocation service is
added.

Shared field offsets select scalar leaves and skip padding. Signed integer
widths use the existing release wrapping rules; F32 and F64 use their own negation
instructions. Fixed arrays use a bounded element loop rather than one compiler
local per element. Empty images perform no leaf operation. Existing debug-mode,
relative-reference, nonfixed and unsupported layout guards stay in place.
No new call-result or parameter ABI is introduced.

## Correctness checks

Twenty-five native-first families pass at O0 and O2, with all fifty positive
pairs checked in Node and Wasmtime. They cover signed MIN/MAX at all four
widths, mixed widths, nested arrays/structs, data-memory and borrowed sources,
by-value array/struct arguments and results, later argument mutation, inline and
callback bodies, recursion, captured results before defers, globals, double
negation, projected temporary reads, early returns, break, continue, effectful
indices, zero arrays, readonly fields, literals/defaults and nested construction.
Completed-owner and restored-top checks are included.

Two complete memory observers use a padded mixed-F32/F64 struct. A reference
write keeps the actual field path live. At the checkpoint the host seeds
signaling-NaN payloads, source padding, destination padding and sentinel bytes.
The resulting sign bits and payloads must match exactly. Source bytes and
padding remain unchanged; destination padding is not written by the arithmetic.
The Memory 0 case checks its live named frame and its completed top. The data
case checks all Memory 0 and data-memory bytes, the u32 count prefix, the live
and completed data tops, and the memory namespace. Valid missing-negation,
wrong-op, wrong-offset and wrong-memory controls fail named image assertions.
All eighteen healthy/control image checks pass.

A separate observer checks the actual Memory 0 top at every loop head and after
the loop, before the function frame is released. A missing continue restore
fails there, so final function cleanup cannot hide a leaked operand temporary.
All four healthy/control loop checks pass.

The first image helper expected the data field's offset to be6. The actual
store includes the u32 prefix and has offset10. Five healthy/control checks had
completed before this regex assertion stopped setup. The original failure and
scope note are preserved. Only the test selector changed; no compiler rebuild
was needed. The corrected eighteen-check run passed.

## Independent audit and separate native defect

A read-only native Codex bug search found no confirmed defect in the Wasm change.
Its requested signed limits, borrowed/data sources, nested shapes, projections,
exits, padding and FP payload checks were added.

A separate adapting-array probe exposed a pre-existing P1 native backend defect.
The source is valid, but negation into a larger limited receiving type uses the
receiving capacity for arithmetic. Saved C reads element2 from a two-element
operand and leaves the receiving length unset. Binary arithmetic has the same
failure. Native failing-first records are preserved outside this feature's
positive results. A separate native fix will compute at the operand's fixed
layout and then use the existing adapter. The Wasm negation path rejects this
layout change before output; it leaves no partial module. The unsafe native
case is not counted as passing differential coverage.

## Validation and limits

The final correctness-only suite passes 3,359 Wasm checks, including all forty
complete memory matrix cases. The native baseline passes 2,358 frontend,
1,155 generated-C and 1,327 TinyCC groups, plus all other baseline groups.
All 52 exact comparisons pass. All 798 unchanged parent fixture modules are
byte-identical. All 78 compiler/support and 4,952 validation input hashes match
the frozen tested executable and source.

Leaf work grows with visited numeric fields and array elements. Stable operands
need no initial whole-image copy for negation. Producers can need an existing
stored-value temporary, and assignment uses its existing complete RHS temporary.
These are source-level costs, not measurements of runtime, compiler allocation,
RSS or physical memory. No timing, performance gate or measurement lease is
part of this correctness-only work.

Selected compiler SHA256:
`390d3d3fcfe3e22f49dc8edd1ae24932f09eceec64caa027b8327a92ae4feb49`.
Selected records and raw hashes are in the
[archive manifest](fixed-negation/archive-manifest.json). Raw binaries and full
records remain in `/tmp/goose-wasm-fixed-negation-20261108`.
Execution evidence is Linux native and the configured Node/Wasmtime hosts.
The complete backend remains unfinished. Layout adaptation, general binary
aggregate arithmetic and other compound paths still need compilation work.
