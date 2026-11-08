# Fixed-array negation at limited destinations

Fixed-array negation now constructs a static-capacity limited receiver with the
same element type. The source count must fit the receiving capacity. A checked
child image covers only the live arithmetic payload after the shared length
prefix. The existing negation helper writes numeric leaves there. The existing
array-header helper writes the source count after arithmetic completes.

The original complete fresh-owner proof remains in force for frame owners,
incoming results, protected temporaries and nested data-memory children. Child
bounds include the prefix, payload and owner-relative offset. No new descriptor,
compiler field, allocation service or operand copy is added. The arithmetic loop
follows the source count, including zero. The owner still reserves its declared
receiving capacity through the existing storage plan. The constructor leaves padding and inactive capacity
bytes untouched. Source temporaries remain live through the header write.
Assignment keeps its existing protected complete-RHS copy. That copy can change
inactive destination bytes; no unchanged-byte claim is made for those assignment
slots. The language permits stale limited-array references to observe another
value of the correct type (§9.4).

## Correctness evidence

Seven native-valid cases failed at the old exact-layout negation guard. They
cover declarations, assignment, by-value arguments, results, fields, F64 and
numeric structs. The selected parent compiler and source hashes are recorded.
The prior native arithmetic repair supplies the correct native comparison.

Twenty-three positive families now pass at O0 and O2 in native code, Node and
Wasmtime, with completed-owner checks. They include all four signed widths and
MIN/MAX wrapping, zero-length local sources, equal and larger capacities,
readonly borrowing, captured call results before defers, later argument effects,
globals, fields, nested numeric structs, data-row assignment and loop exits.
The shared multi-context function has one declared reference argument and an
actual hidden stack-base parameter at both optimization levels. This exercises
data construction under runtime-selected bases. It makes no recursive call.

Forty-six Node observer/control checks pass. The padded mixed-F32/F64 cases seed
source NaN payloads and signed zeros, source padding, destination padding,
inactive capacity and sentinels. They compare complete Memory 0 and data-memory
images, live tops and completed owner state. The data case checks both the outer
u32 row count and the inner limited-array count. Valid missing-negation,
wrong-operation, wrong-offset, wrong-count, wrong-bound and wrong-memory modules
fail named image assertions.

Capacity 255, 256, 65535 and 65536 checks cover both count-width transitions.
Their observers seed the whole receiving image, including upper count bytes,
and compare all bytes after construction and completion. Valid wrong-count
controls fail the expected image assertion. A separate loop observer checks the
actual Memory 0 top on every head. Removing source-temporary cleanup fails at
the next head, before final frame cleanup can hide it.

The complete Wasm suite passes 3,543 checks. Native baseline passes all 18 groups,
including 2,410 frontend, 1,181 generated-C and 1,356 TinyCC checks. All 52 exact
native-output/diagnostic comparisons pass. All 848 prior Wasm fixture modules
are byte-identical using completed full-suite outputs, without guest reruns.
Execution evidence is from Linux. No performance measurement was run under the
correctness-only owner directive.

## Preserved failures and limits

The first preparation used a mixed integer/float numeric struct, which the
frontend rejects. Three later audit helpers assumed the negation diagnostic for
cases stopped earlier by existing layout or call guards. All raw failures remain
unchanged. A final file-only audit verifies all ten completed native-first cases
and their exact Wasm reasons; passed guest runs were reused by hash.

A later fixture held a nonfixed row owner across a recursive cycle. The frontend
correctly rejected it under §7.8, before C emission. The replacement uses two
valid call contexts and a live parent row. Only the two previously unrun
supplementary families ran afterward; no compiler rebuild was required.

Arrays with compound array elements and zero-sized aggregate call results retain
their three specific guards at O0/O2, with no partial modules. Variable/growing
receivers, general arithmetic and other layout conversions remain separate.
This does not complete the backend.

Raw records remain at `/tmp/goose-wasm-negation-adaptation-20261108`. The
[archive manifest](negation-adaptation/archive-manifest.json) records frozen
source/input hashes, compiler identities, commands, failing-first evidence,
controls and final validation. Binaries and full generated artifacts stay in the
raw directory.
