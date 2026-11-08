# Limited-array values in nonfixed receiving arrays

The direct Wasm backend now constructs a variable, growable, runtime-limited
or unsigned-LEB-prefixed array from a static limited-array value with the same
element type. The native-valid parent programs were rejected by the Wasm target.
The parent is `ca0a5a7b5c0f105d742fa1cdc9e16c488a7b4da3`.

The tested Release compiler SHA256 is
`5423e0e29e1c9f74f46ef45bbc7bc2a55f99508f446fc2d1fd87a35b4b6f7b37`.
Both compiler builds, their source hashes and the assertion-enabled build flags
are retained in the archive.

## Construction

`InitLimitedArrayValue` admits only resolved static-limited sources and matching
fixed element layouts. A reference, call result or temporary field uses the
existing checked read-place service. The source is evaluated once, then its
active count is captured once. A call result retains its declared source layout
until construction finishes.

The declared destination count field must fit the source's active count.
A smaller stored prefix gets a runtime range check before any receiving
allocation or write. A static source capacity that already fits proves this
check unnecessary. Runtime-limited arrays use the layout authority's u32 fields,
with both length and capacity set to the copied active count. The source's spare
capacity does not become the new capacity.

Unsigned LEB destinations compute the prefix width from the captured count,
then write the prefix bytes into the checked reservation. The payload byte count
is active count times element size. The checked fixed source span proves this
product fits memory32; a separate u64 addition check includes the destination
prefix. The source's own prefix and field offset are retained when its payload
is copied. A stored source needs no intermediate owner. Computed sources use
the existing checked fixed temporary.

Receiving storage uses the existing symbolic stack plan. Local receiving
cleanup is attached to the declaration's scope before source temporary scopes
are opened. Source temporary cleanup therefore leaves the receiver live.
Globals retain their existing persistent lifetime. Ordinary reference elements
are copied as references; their pointees remain shared.

The observed data-array pointers stay in Wasm locals. Their source frames and
data images are checked separately. Growable arrays retain their existing
Memory 0 headers. No general nonfixed argument/result ABI, descriptor landing,
pool storage or conversion between different element types is added here.

## Failing-first and focused checks

All 55 final fixture families execute successfully in the preserved parent
native compiler. The same sources fail at the parent Wasm target's missing
conversion checks. Forty-six existing parent producers are reused after source,
compiler, stdout, stderr and golden checks. The original command paths are
preserved; `parent-reuse.json` gives the source and copied record directories.
Nine extra parent families are produced separately.

The focused run has 110 native/Node/Wasmtime pairs at O0/O2. It covers stored
values, ordinary references, intrinsic and deferred results, source effects,
padded structs, reference elements, data fields, a field at a nonzero offset,
dynamic memory namespaces, globals, loop exits, early function return, empty
arrays, and counts 127, 128, 255, 256, 16384 and 65536. The runtime-limited
capacity checks distinguish active count from source capacity.

A read-only source bug search found an error in the first prototype's width
lookup: `LenStore` requires a static capacity. The prototype used it for a
runtime-limited destination. Its Release executable then rejected a valid
256-element conversion with a false 255 limit. The exact native-valid test
failed in `runtime-width01` and passes in `runtime-width02`. The fix uses
`ArrayPrefix(...).storage`, which also covers runtime headers. The old compiler,
source and failure are retained. No prototype timing or full-suite run occurred.

A second compiler has C++ assertions enabled. It compiles and executes all 110
pairs under Node; every generated module is byte-identical to the Release
compiler's matching output. The worker ran no builds or guests, and its source
report is kept separately from execution evidence.

## Full-image observers and controls

The padded-element observer checks the complete Memory 0 source frame and the
complete receiving data memory. It seeds active source padding, inactive source
capacity, future receiving storage and an adjacent sentinel with distinct bytes.
The copy must include all bytes of each active element without copying spare
capacity. Live and completed stack tops are checked after explicit checkpoints
and `_start` completion.

The LEB observer checks a dynamic two-byte prefix, the complete 128-element
payload, unchanged inactive source bytes, the data sentinel and complete Memory 0.
The empty-result observer checks a real source call with its one-byte temporary
live, then checks that the temporary is gone and the receiving prefix remains
live. Both variable and runtime-limited receiving headers are covered.

Healthy and validated damaged modules contribute 60 logical checks at O0/O2.
Controls change copy length, count width, memory identity, LEB continuation bits,
computed prefix width, source reservation, source cleanup, receiving cleanup and
frame restoration. The required assertion identifies each damaged behavior;
an arbitrary rejection or trap is not counted as a pass.

The range-failure checks use valid lengths 256 and 65536 that exceed u8/u16
receiving prefixes. Native execution fails with its stored-length range message.
Node and Wasmtime must report `array length exceeds stored prefix`, error 15.
Both host adapters implement that message. Exact-message checks precede the
source path and cannot pass on a filename substring.

The failure observer checks full Memory 0 and data images, with no receiving
allocation or write. The failed activation retains its source frame and cannot
run again. This does not claim terminal-unwind cleanup. A valid inverted range
guard must fail the observer after it incorrectly completes the conversion.

## Final verification and limits

The [final record](limited-array-conversion/final-validation.json) gives actual
full-suite counts, native groups, 52 exact comparisons, unchanged parent module
identities, and frozen-source/test/compiler checks. The archive retains raw
subprocess output, status and command records, prototype failures and build
identities. Raw files remain under
`/tmp/goose-wasm-limited-array-conversion-20261108`.

This work is correctness only. No measurement lease, benchmark or timing
acceptance is used. The new classifier adds compiler work at receiving
construction sites. Runtime bookkeeping uses a fixed number of locals; LEB
prefix loops are bounded by the memory32 source count. Copy work and receiving
storage grow with active payload size, as required for an independent value.
No compiler-allocation or physical-memory cost is claimed.

Four- and five-byte LEB counts were not allocated in these tests. Different
nonfixed source layouts, general block/conditional array construction, general
array-value calls, nonfixed fields, pools,
relative references, slices, byte views and host/worker adapters remain separate
compilation work. The full backend is still incomplete.
