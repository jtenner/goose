# Fixed numeric binary arithmetic

The direct Wasm backend now constructs fixed numeric arrays and structs for
`+`, `-`, `*`, `/` and `%`. Scalar operands work for multiplication and division
when the frontend permits one scalar type across all leaves. Integer and float
leaves use the existing scalar arithmetic helpers. Numeric struct fields and
fixed-array elements retain their declared widths. Padding is not arithmetic
output.

Construction uses the existing checked fresh destination. An exact receiver
uses its complete image; an adapted static limited array uses a checked payload
child after its shared length prefix, followed by the source count. Calls,
arguments, returns, fields, data rows, nested expressions, discarded binary
results and protected ordinary assignment use this path. General arithmetic
adaptation to variable or growing arrays is not included.

## Operand order and storage

Operands run left to right. A scalar operand is captured once. If a right
operand can change its left source, the left aggregate is copied to one private
Memory 0 temporary before the right operand runs. The effects scan stops after
64 syntax nodes and conservatively selects a copy when that limit is reached.
Calls, writes and control also select the copy. Source-expression temporary
owners end after this copy; the private value remains live through right-side
effects and arithmetic. Its restore action is registered before source
construction, so early exits retain the existing cleanup order.

The scan has a fixed per-expression bound. Arithmetic work follows the number
of numeric leaves. A selected snapshot copies the complete fixed source image
and uses its byte count in the existing frame allocator. It adds no persistent
compiler table or runtime allocation service. Nested effectful expressions can
keep several existing frame reservations live. These are source-level cost
limits, not measured runtime or physical-memory claims. The owner directive
excludes performance measurement from this work.

Ordinary assignment retains its complete-RHS protection. Integer failure in a
later arithmetic leaf cannot partially replace that assignment's permanent
destination. This does not claim trap atomicity for compound assignment, which
is not implemented here.

## Correctness evidence

Thirty-five native-valid cases fail on the parent Wasm backend before this
change. Thirty-eight positive families pass at O0/O2 in native code, Node and
Wasmtime, with completed-owner checks. They include all five operators,
unsigned wrapping and division, signed-width limits and Euclidean modulo,
F32/F64 mixed fields, NaN/infinity, scalar broadcasts and aliases, actual
recursion, callbacks, reference results, effectful indices, a conservative
scan-limit case, empty-array operand effects, early return/continue, large
arrays, static limited destinations and nested data-memory destinations.

Thirty exact FP image/control checks cover Memory 0 and separate data memory.
They seed source padding, destination padding and sentinels. Signed-zero and
infinity bits are exact; NaN results must be quiet, with permitted payload/sign
variation. Every other byte is checked, including unchanged source NaN bits.
Valid wrong operations, offsets, padding stores and memory selection fail named
image assertions. Four snapshot checks inspect the complete image while the
right call runs and after the result is stored; valid reads from the changed
original source fail. Four live-loop checks include a valid missing-restore
control that fails at the next loop head. Six native/Node trap checks verify
zero division/modulo and signed division overflow, with the permanent Memory 0
image and print/snapshot owners checked after failure.

The complete Wasm suite passes 3,815 checks. The native baseline passes all 18
groups, including 2,486 frontend, 1,219 generated-C and 1,394 TinyCC checks. All
52 exact shared-backend comparisons pass. All 894 parent Wasm fixture modules
are byte-identical using completed suite outputs, without guest reruns for the
identity comparison. Execution evidence is from Linux. No timing or measurement
lease was used.

## Preserved preparation failures and limits

One early fixture requested `.cap` on a fixed array, which the frontend rejects.
The corrected `.len`/element projection is tested separately. The first snapshot
observer omitted the getter's call-counter write from its expected image. The
first overflow assertion assumed the Wasm message for native execution; the two
runtimes use different text. A reuse helper then correctly refused artifacts
with different embedded source paths. All failures remain unchanged. The final
continuation verifies saved artifact hashes and reuses completed checks before
running the missing overflow cases.

Read-only native Codex bug searches found no confirmed defect in the new binary
snapshot path. Separate native-valid reproductions confirm that compound
aggregate assignment and discarded aggregate unary minus still need lowering.
They are not claimed fixed here. Other limits include variable/growing arithmetic
receivers, arrays with compound array elements, zero-sized aggregate call
results, general slices, root/pool/relative values and remaining host adapters.
The complete multi-memory backend is not finished.

Raw records are in `/tmp/goose-wasm-fixed-binary-math-20261108`. The
[archive manifest](fixed-binary-arithmetic/archive-manifest.json) records source
and input hashes, compiler identity, commands, failures and final checks.
Binaries and full generated artifacts remain in the raw directory.
