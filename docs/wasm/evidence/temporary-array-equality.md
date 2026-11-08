# Temporary fixed-array equality

Fixed-array equality now keeps temporary operands live and supports an
effectful right operand. Same-type array equality captures the complete left
value before the right operand runs. It uses the existing checked temporary
owner and copy service. Scalar/reference element comparison then uses the
existing length and element rules. The boolean result is saved before cleanup.
Stable non-effectful comparisons keep their existing emission path.

The frontend adapts different array types to whole comparison slices. This has
a different rule: the left address and length are captured, but the elements
are read after the right operand. The new path accepts only two frontend
`cmpview` nodes with no bounds or from-end flags, and only fixed or statically
limited array roots. It retains temporary roots through comparison. This does
not add general slice values, function parameters, results or slice operations.
Explicit slices and nonfixed comparison views keep exact target guards.

## Native-first behavior

Thirty-one families cover O0 and O2. Both Node and Wasmtime pass all sixty-two
case/optimization pairs. Cases include left/right/both results, literals,
defaults, blocks, projected fields, inline/callback/global uses, fixed/limited
length differences, empty images, bool, f32/f64, NaN and signed zero, shallow
reference identity, optional references, and RHS reference-slot rebinding.
Return, break, continue and short-circuit cases check evaluation and cleanup.
Complete-owner observers check restored tops after completion.

The native value-copy probe prints true then9 when the RHS changes the original
left array but returns its old values. A separate adapted-view probe must read
the new left element value. Another grows a limited source to length3: the
comparison keeps its captured length2 while reading the new elements. A
reference-rebinding case keeps the old address; projected temporary and reversed
fixed/limited cases check the other view paths. No value-copy rule is inferred
from the view tests or vice versa.

A complete Memory 0 model seeds the uninitialized reservations and sentinel
bytes. At the RHS print checkpoint it checks the unchanged left snapshot, the
mutated source and the still-unwritten right result image. After comparison it
checks the complete returned image and restored tops, then waits for guest
completion and checks the full final image. Valid missing-capture, early-release
and missing-restore modules fail named assertions. All eight healthy/control
image checks and four native-valid explicit-slice/nonfixed-view guards pass.

## Preserved errors and audit

The first native extra set stopped on a block operand without required
parentheses. Its invalid source and failure remain separate. Passed producers
were reused; the remaining corrected cases passed. A helper preparation error
changed a truncation marker before lookup; it started no candidate test.

The first candidate passed forty-four positive pairs, then stopped on a valid
zero-length comparison. The frontend had adapted its different array types to
whole comparison slices, which scalar emission did not support. The build02
extension handles only those fixed comparison views. The valid zero-length
case also proves that the RHS effect is not skipped. Both compiler versions
and the exact failed command are preserved.

A preflight found the old effectful-equality test still expected rejection.
It now requires native output in both engines and restored owner state. Unary
array operators retain their own guard. Four expected redundant-reference
warnings were marked at EOF in one fixture; both modules remain byte-identical
to their completed pre-comment versions. No compiler rebuild was needed for
test corrections.

A read-only native Codex bug search inspected the value path and then the
comparison-view extension. It found no confirmed defect. Its requested alias,
length, projection, exit, short-circuit and FP cases were checked natively and
in both Wasm engines. No worker ran code or changed production files.

## Costs and remaining scope

No compiler field, IR node, runtime descriptor or allocation service is added.
Compiler closures are stack values. Copying a left fixed image does work and
uses addressable temporary bytes proportional to its image. Projected producers
can need a containing temporary too. This is required to preserve an independent
value across RHS effects without a new alias-proof mechanism. View comparisons
retain the original owners instead. Element comparison is linear in the visited
elements and stops at the first mismatch. These are source-level facts, not CPU,
RSS, allocation, runtime or physical-memory measurements. This thread is
correctness-only and has no performance gate or measurement lease.

General slice equality, nonfixed operand snapshots, nominal-element equality,
array unary/binary arithmetic and other compound lifetimes remain separate
compilation work. Zero-byte call result/parameter transport is not expanded;
empty fixed defaults can compare without that ABI.

The final correctness-only suite passes 3,187 Wasm checks, including all forty
complete memory matrix cases. The native baseline passes 2,308 frontend,
1,130 generated-C and 1,302 TinyCC groups, plus every other baseline group.
All 52 exact comparisons pass. All 736 unchanged parent fixture modules are
byte-identical. All 78 compiler/support and 4,899 validation input hashes match
the tested source and executable.

Selected compiler SHA256:
`d7a04fe9027b226765e0486fa0dd77cd2a0c2ad8d96c708f10a9d4b9c753ab61`.
Selected records and raw hashes are in the
[archive manifest](temporary-array-equality/archive-manifest.json).
Raw binaries and complete records remain in
`/tmp/goose-wasm-temporary-array-equality-20261108`.
Execution evidence is Linux native and the configured Node/Wasmtime hosts.
The full backend is not complete.
