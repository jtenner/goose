# Fixed-size array results

Positive fixed and statically limited array images now return through the
checked destination ABI used by fixed nominal results. Ordinary signatures
have no scalar Wasm array result. The private I32 destination follows any
data-stack base. Inline and callback bodies use checked real receiving owners.
The callee writes its full return image before defers and frame/data cleanup.

Fresh declarations, global initializers, arguments, fields and exact assignments
accept these results. Packed data fields use a Memory 0 landing image before
the cross-memory copy. Assignment commits only a completed temporary image.
Fixed array block and conditional producers use the same construction path.
Array-reference results keep their existing scalar reference ABI; the new
routing checks the actual return type before selecting destination construction.
Zero-byte fixed result transport, nonfixed results, layout adaptation, unnamed
field/index/length consumers, multiple results and remaining nonlocal calls
stay separate compilation work. An empty limited array with a stored length
header has a positive image and is supported.

The native-first set has twenty-seven families at O0 and O2. It covers direct,
inline and callback calls, early and tail returns, recursion, forwarding,
global/discard/argument use, defer mutation after capture, fixed/limited images,
nominal/reference elements, large frame growth, dynamic data-stack bases,
mixed parameters, float signed-zero/infinity and bool results, and array-reference
copy/discard controls. Both engines pass all fifty-four functional cases.

A complete Memory 0 model seeds inactive capacity in a nine-byte source image.
It checks the separate argument snapshot, parameter and local copies, returned
image before the defer write, permanent target before/after commit, sentinel
bytes and actual live/completed tops. Valid short/long/omitted/wrong-destination,
early-target and missing-restore controls fail specific assertions.
Native-first divide failure preserves the complete permanent target image;
an invalid data-field target fails before the RHS call or temporary starts.
Native-valid zero-byte, nonfixed and adapting result cases retain exact target
diagnostics and leave no partial module.

A second observer covers block and both conditional branches constructing array
fields directly in data memory. It seeds both data memories, compares their full
images, verifies Memory 0 remains unchanged, and checks each scratch owner's
actual top before the following field runs. Inactive literal capacity remains
seeded and unchanged; it is not assumed to be zero. Valid wrong-width, omitted
header and wrong-namespace stores fail the named image assertion. Intermediate
tail checkpoints also preserve field order. The observer waits for completed
guest ownership and checks all three restored tops.

A read-only native Codex bug search found no confirmed reachable defect. It
asked for an array-reference result control and a focused nested data-constructor
image check. Those native-first, both-engine and image controls were added with
no compiler change. The earlier worker scope contained the first twenty-five
families and the initial owner/check helpers; it was not a second review of
the later observer. The tested source remained frozen after the first build.

The result ABI adds no new runtime descriptor or compiler field. Live Memory 0
landing bytes and byte-copy work grow with the complete image and active calls.
Cross-memory construction needs its landing copy. Constructors still perform
the work required by their elements. These source-level costs preserve value
isolation, defer order and memory identity. They are not measurements of runtime,
compiler allocation or physical memory. No performance gate, timing run or
measurement lease is part of this correctness-only work.

The final correctness-only suite passes 2,833 Wasm checks, including all forty
complete memory matrix cases. The native baseline passes 2,198 frontend,
1,075 generated-C and 1,247 TinyCC groups, plus all other baseline groups.
All 52 exact comparisons pass. All 634 unchanged parent fixture modules are
byte-identical. All 78 source/support and 4,785 validation input hashes match.
The complete selected checks passed with the same frozen executable.

The selected compiler SHA256 is
`111b80478b0a215cc0d50a2fe3b91774b6e40275c477d3537fea3f979bb8567e`.
Selected records and raw hashes are in the
[archive manifest](array-results/archive-manifest.json). Raw binaries and full
records remain in `/tmp/goose-wasm-array-results-20261108`.
Execution evidence is Linux native and the configured Node/Wasmtime hosts.
No performance or cross-platform runtime acceptance is claimed. The complete
backend remains unfinished; scoped temporary reads are the next compilation gap.
