# Fresh fixed packed struct owners

This step adds stored fixed structs to the direct Wasm backend. It is part of
Stage D. The full backend task remains open.

## Behavior and limits

Local and global ordinary fixed structs use Memory 0 storage. A stored struct
has a place, not a scalar Wasm type. Sizes and offsets come from `ValueLayout`,
including packed fields, explicit pads, bare-pad alignment, empty structs,
generic instances, nested admitted structs and inline scalar/reference arrays.
The bounded layout query checks products and sums before narrowing to Memory32.
The native unbounded layout interface retains its previous behavior.

Fresh construction accepts literals, checked defaults and exact-layout copies.
It writes fields in declaration order and copies a child before a later
initializer can change its source. Ordinary reference fields retain eight
stored bytes and keep their referenced targets on copy. Runtime reference
currency follows the existing thin or packed-address ABI. The support and
storage passes follow recursive reference graphs, including data-array
references hidden in struct fields.

Reads and updates accept scalar fields, nested fields, ordinary struct
references, reference fields and reference-valued array elements. Assignment
captures its destination before RHS effects. Inline array fields use existing
scalar/reference indexing, length, capacity, push, pop, clear and exact-copy
operations. A local array reference can use the existing iteration path.

Direct field-path iteration, whole-struct assignment, struct value comparison
and rendering, by-value aggregate call boundaries, aggregate temporaries,
compound array elements, variable/resizable fields, roots, pools, relative
references, slices, enums and serialization still need later lowering. They
retain target diagnostics. If optimization removes a call boundary completely
and leaves a fresh literal, the existing fresh-construction path can accept it;
this is not a by-value result ABI.

Ordinary reference-returning calls can feed a fresh exact copy. Discarded
struct-reference call results use their declared reference currency. They
do not force an unsupported struct-value read. Direct struct values still have
no scalar Wasm representation.

## Validation state

The final compiler is preserved as
`/tmp/goose-wasm-fixed-struct-20261107/build04/goose-tested`, SHA-256
`7fdb4c2236fcfddb599c0426e23ba5547779ec0ef0f27790545a886b4edd1d54`.
Its C++ sources were frozen and verified against its build manifest.

Completed targeted and final-suite records cover fourteen native fixtures at
O0/O2 and twenty-eight validated struct-fixture modules under Node and Wasmtime, completed frame/data owners,
real frame growth, constructor effects, nested copies, all array families of
ordinary struct references, field rebinding and hidden reference ABI width.
A valid wrong-store-width module is independently validated, then fails the
specific neighboring-field assertion in both engines. The numeric query test
covers pads, empty objects, reference cycles, cached limits and overflowing
products/sums without allocating the declared images.

Seventeen native-valid admission cases distinguish unsupported operations from
an optimized fresh literal. Three compile-only layout/frame limit cases reject
before output at both optimization levels. The exact initial push diagnosis
inputs fail before the repair and pass after it. The final complete suite passed 590 checks under Node 24.22.2 and Wasmtime
Python 49.0.0, with wasm-tools 1.262.0 validation. Its count includes executions,
diagnostic cases and static controls. The full native baseline passed on the
same repaired compiler, with recorded device/platform/JIT skips. These results
are from Linux x86-64.

All 52 saved C/report/older-Wasm comparisons, all 100 pre-struct Wasm module
pairs and 14 earlier accepted struct-module pairs remain byte-identical after
the final repairs. These are exact output comparisons, not 166 native execution
tests. Final fixture-module hashes and local counts are in `final-modules-repaired.json`.

## Independent review and repairs

The [Astra review](fixed-structs/astra-review.md) inspected all 30 frozen scope
files and the saved evidence without execution. It found two source defects.
Both were independently reproduced with the preserved pre-fix compiler before
the repairs, at O0 and O2:

- An explicit `&field` used as a scalar value returned an address. Integer and
  false-bool cases produced wrong values in both engines, and an f32 module
  failed validation. Scalar field decay now uses the normal stored-type load
  and conversion; references and aggregate address handling retain their paths.
- A discarded ordinary struct-reference call result reached the struct-value
  rejection. The declared single reference result is now emitted and dropped
  for calls and retained inline blocks. Live by-value aggregate guards remain.

The exact failing inputs now pass validation and both engines. Expanded cases
check every integer width, bool, f32/f64, nested and reference receivers, thin
and packed references, reference identity, used and discarded results, inline
cleanup effects, named/block callbacks, and exact copies. Added nested/global
reference-array-field cases check two distinct data-memory targets, rebinding,
copy independence, used/discarded push/pop results and neighboring fields.
Completed owner-state checks also pass. The discarded minimal call module has
no aggregate `memory.copy`; the O2 inline case has no out-of-line touch function.

The original review remains unmodified and refers to the pre-fix hashes. These
small repairs were verified by source inspection and discriminating execution;
no second independent review is claimed. `review-resolution.json` records their
scope and evidence. The deliberate explicit-reference bindings have expected
warning markers; no native warning was suppressed.

## Footprint and cost limits

The first fresh limited-array-field literal implementation reused four scratch
locals but still added three more for each element through shared helpers.
The saved 32/256-element checks used 116/788 locals. The repair reuses address
scratch and the captured value only on the fresh field-constructor path. Both
sizes now use 22 locals at O0 and O2. Module sizes fell from 8,876 to 8,812 bytes
and from 66,403 to 64,347 bytes respectively. Both versions produce the same
checked result. This is a static footprint result, not a runtime speed result.

Frames reserve the sum of bound slots per activation; this step does not reuse
slots across lexical scopes. Memory growth retains pages. Copies take time
proportional to the copied byte count. Layout graph traversal and caches use
compiler memory proportional to reachable types, fields and owners. Literal
code and evaluation still grow with the number of initializer expressions.
There is no new guest heap or host bridge for aggregate operations.

Deep field selection still repeats type-path lookup and can perform quadratic
compiler work in path depth. A dynamic fixed-copy helper can use quadratic
memory-pair dispatch code within the 65-total-memory limit. Neither practical
cost has been measured. See `cost-handoff.json` for the queued source/build and
workload plan. These are unverified cost risks, not additional confirmed defects.

Guest throughput, compiler CPU/RSS/allocation costs, native cross-platform
execution and the full dispatch/layout/EH/worker matrix remain unmeasured for
this step. No minimal-memory or end-to-end speed claim is made. The measurement
handoff must compare the preserved pre-struct compiler with this exact compiler
for shared native callers, and compare matched native/Wasm field, copy and
constructor workloads in a new coordinated lease turn.

## Evidence integrity

Raw attempts remain separate under `/tmp/goose-wasm-fixed-struct-20261107`.
The initial native fixture errors were invalid inputs and were corrected before
being counted. A second native wrapper incorrectly retained the first output
directory and replaced its aggregate lease/summary files. The original first
per-case records and first release check remain. The actual second aggregate
records were copied into their proper directory with a correction record; the
original aggregate files are not reconstructed or claimed unchanged.

The second handoff also claimed a fresh probe before checking a failed verifier
status. This was corrected immediately. The actual deferred probe passed after
E22 released. Later wrappers refuse to overwrite a unit record, and every later
handoff checks the verifier's actual exit status first. No performance sample
was taken, changed or interrupted. Source packets for the first three compiler states
have been reconstructed and verified against their original source hashes.
The separate final repair packet matches build04's frozen hashes. The complete
final native and Wasm runs have explicit exit, reaping and release records.
