# Initial inline scalar-array layouts

This stage adds fixed arrays and static-capacity limited arrays whose elements
are scalars or supported ordinary references. It does not complete stage D or
the full backend. Variable arrays, varints, compound elements, slices, byte
views, serialization, copies, destination construction, and by-value array
arguments/results remain pending. Unsupported constructors receive target
diagnostics before module output.

The baseline is data-stack commit
`69ca4f1f661159929f228799556bc4ddb8a5f2a9`. Native C lowering and runtime source
are unchanged. Numeric sizes and prefix widths come from `ValueLayout`.
Fixed arrays have no metadata prefix. Limited arrays use their specified
smallest length field, with no implicit element padding. The admitted inline
owners reside in Memory 0. Their references are thin i32 SSA values even when
other references in the same program need packed i64 addresses. Stored inline
array references still occupy 8 bytes; stored growable owner references still
occupy 16 bytes. Dynamic scalar-store helpers widen thin reference values to
their stored width. Separate zero-size owners reserve one byte each for
address identity; this does not add bytes inside the value representation.

Limited push checks capacity before storing or publishing a new count. Pop
and clear update the inline count without changing a data-stack top. All
scalar access widths and the existing reference-element rules are reused.
Addressable locals use the function's authoritative Memory 0 frame. There is
no new guest heap or per-iteration allocation. Frame slots do not yet reuse
storage across disjoint lexical scopes.

`WasmModule::ZeroData` reserves static zero-filled ranges without a compiler
buffer or a serialized data segment for unused capacity. Actual initialized
bytes retain their offsets in sparse active data segments. The minimum memory
and initial frame top cover the entire reserved range. The encoder unit checks
interleaved initialized bytes, two gaps, overflow rejection, top alignment,
and engine-visible zero contents. It emits 529 bytes for a module with more
than 128 KiB of reserved zero space. The original encoding remains identical
when no sparse reservation is used.

## Failing-first iteration repair

Two independent read-only Sol searches inspected the new code. One identified
an indexed array-reference iteration risk. It was reproduced before any fix
on compiler SHA256
`1b8baa6698b5d7f33611137a41f1037129d1a061092c35e338092e8381d0adc5`.
Native C produced `1, 20, 30` on separate lines after an array's reference slot
was rebound. The validated Wasm module produced `1, 2, 3`; a limited-array
variant stopped after `1`. Node and Wasmtime agreed. These are native-valid
inputs, not unsupported-type diagnostics.

The native rule snapshots index values but rereads references on the sequence
path at each loop test. A call or temporary used as a root runs once. When an
index emits statements, the native emitter captures its parent view before
that index runs. The Wasm repair implements those rules with a small indexed
walk plan. It captures indices outside the loop, freezes the required prefix
before an effectful index, and reloads the remaining reference slots. The
direct-owner and mutable-identifier loop paths retain their previous lowering.

Regression cases include fixed and limited references, mutable index variables,
index-call counts, a call-returned root, nested paths, mutable root references,
by-reference elements, and an index that rebinds its parent reference. Four
cases at O0/O2 give eight wrong-output comparisons on the pre-fix executable.
The same source now passes both engines and completion-state checks. The
original probe used the wrong owner-check mode for Memory-0-only modules;
that setup failure is preserved outside the source tree and is not evidence
of a stack leak. The later before/after checks use the correct mode.

The walk plan adds a compiler vector per indexed sequence path, with one vector entry per retained path index. Type and layout queries can
repeat across nested steps; their compiler cost is not measured. Captured values are
Wasm locals. Loop tests perform the reference loads needed for the language
rule. There is no runtime heap allocation for the plan. This is a narrow Wasm
repair; the C emitter and shared interfaces were not changed.

## Additional failing-first checks

The inline size guard originally called `Type(element)` and then `Size(element)`,
which validated the same element again. Nested array-reference types multiplied
that work recursively. Native emission accepted depth 28, while the Wasm
compiler exceeded a five-second compile-test limit. A depth-40 input also hit
the limit on the preserved executable, with its killed child exit recorded.
The guard now uses `FixedSize(element)` after the existing validation. The same
source compiles and runs at O0/O2 under both engines. The permanent regression
uses the five-second test limit. This is a functional limit check, not a timing
benchmark or a measured compiler-speed ratio.

Array `==` and `!=` also reached the generic scalar comparison and compared
header addresses. Native-valid fixed, limited and growable arrays with equal
values therefore compared unequal. The same programs now use a length check
and an element loop. Scalar floating-point comparison retains IEEE behavior,
including equal signed zeros and unequal NaNs. Reference elements compare
stored reference identity. Tests include dynamic-memory array parameters,
bool/f32/f64 elements, empty arrays and distinct roots with equal scalar values.
Unnarrowed optional array references retain their prior identity comparison.
The comparison loop has work proportional to the visited elements, uses Wasm
locals and performs no guest heap allocation. General specialization remains
pending. An effectful RHS still requires the pending destination protection
and receives a specific target error before output.

The old emitter also admitted a unary array temporary and wrote an invalid
module. Native execution produces the expected value. The unsupported unary
value now receives the existing destination diagnostic before output. This
change tightens the array-expression gate to identifiers and address forms;
it does not claim to implement elementwise array arithmetic.

## Validation

The repaired Release compiler SHA256 is
`63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`.
Its frozen source and harness hashes are in the manifest. All checks pass:

- 247 Wasm harness checks under Node 24.22.2, wasm-tools 1.262.0 and Wasmtime
  Python 49.0.0, with native O0/O2 output oracles.
- The full native baseline suite, retaining existing platform/device/JIT skips.
- 52 exact native/scalar output and diagnostic comparisons against the
  preserved data-stack compiler.
- 56 byte-identical previously supported Wasm modules at O0/O2 against the
  pre-equality inline compiler `d3969a0a`. The earlier 40-module comparison
  also matched the data-stack compiler.
- Separate failing-first and passing repair records for the indexed path cases.
- Capacity and bounds failures with the matching native reason and no partial
  print, stable references, optional inline-array references in mixed programs,
  zero-length identity, and completed frame/data-top checks.
- Lengths crossing 255/256 and 65,535/65,536 in one instance, with last-element
  reads and pop checks. Eight-byte static-capacity count fields cannot fit the
  admitted inline allocation in Memory32 and are not claimed as runtime-tested.

The nine new positive fixtures include the added value-equality checks. Exact
module sizes and hashes are in the size record.
The large static-capacity global fixture stays below 32 KiB of module bytes;
its unused capacity is not serialized. These size checks are functional file
observations, not timing samples. Existing admitted module bytes remain
unchanged. No new runtime performance, compiler CPU/RSS, allocation-count, or
physical-memory gain is claimed. The planner, sparse data vectors, and added
type checks can affect compiler cost; those costs remain queued for coordinated
measurement. General thin-pointer specialization and the dispatch benchmark
matrix are still pending.

Every resource unit acquired the shared lock nonblocking, reaped all owned
children, released it, and verified owner exit and a successful immediately
released lock probe. No performance samples were taken. The first native-only
fixture draft required an explicit integer cast; its failed setup was preserved
and is not counted as a backend defect or behavior coverage.

Raw source, executables, generated code/modules, outputs, and lease records
remain at `/tmp/goose-wasm-inline-arrays-20261107`. Compact copies retain the
[manifest](inline-arrays/source-manifest.json), [validation text records](inline-arrays/validation.json),
[before](inline-arrays/before.json) and [after](inline-arrays/after.json) records,
[52-comparison summary](inline-arrays/compatibility-summary.json),
[56-module summary](inline-arrays/prior-wasm-summary.json), and
[new module sizes](inline-arrays/module-sizes.json).

Astra independently reviewed all39 changed files and found no confirmed defect.
It verified six executable identities and all56 prior-module pairs. Its
[report](inline-arrays/astra-review.md) retains the exact scope and evidence
limits; this is not a performance approval. The parent later verified the
missing build-input hashes and final module file identities in
[follow-up records](inline-arrays/review-evidence-followup.json). No second
review or new execution is claimed by that file check.


The later [equality validation](inline-arrays/equality-validation.json),
[equality before](inline-arrays/equality-before.json),
[equality after](inline-arrays/equality-after.json),
[compile-limit records](inline-arrays/query-validation.json), and
[compiler identities](inline-arrays/compiler-identities.json) retain the
additional checks and exact preserved executables. The final reviewed source
is the snapshot that produced the 247-check Release result.


A post-review test-only unit on the same preserved compiler covers the proposed
inline-only scalar/reference/optional-reference element equality cases, f32 NaN
self-comparison and inequality, and mixed inline/growable deferred rebinding
during early exit. Native O0/O2 outputs match Node and Wasmtime, and completed
owner-state checks pass. These two fixtures and their runner registration were
added after review. No compiler source changed for this follow-up. See
[the raw text records](inline-arrays/review-coverage.json). The earlier full
suite count remains the recorded 247; these are additional targeted checks.
