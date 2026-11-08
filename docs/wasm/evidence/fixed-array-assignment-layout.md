# Fixed sources into existing static-limited arrays

The Wasm backend now assigns a fixed array to an existing static-limited array
with the same element layout when its count fits the receiver's capacity.
The caller's captured destination is retained across RHS evaluation. The source
is read once. The payload copy runs before the new count store, and both use
that captured destination. Unused receiver capacity stays unchanged.

The new path reuses the existing fixed-array conversion predicate, fixed layout
checks, read-place lifetime, bulk copy and array count store. It checks offset
overflow before adding the count prefix. All four memory-copy modes retain
Wasm overlap semantics. Pure stored values need no extra temporary. Call results
and other value producers retain their existing intrinsic temporary through the
payload copy and count store. Exact-layout assignment keeps its old path.

## Correctness evidence

Twenty-one native-valid families fail to compile on the parent Wasm backend.
The candidate passes all 42 O0/O2 pairs in native code, Node and Wasmtime, with
completed owner checks. The matrix covers stored and copied values, references,
call results, temporary field sources, globals, defaults with element effects,
reference and padded-struct elements, empty results, wider count prefixes,
LHS reference rebinding during RHS evaluation, and both data-memory directions.
The same reference-parameter function runs with Memory 0 and separate data
memories. No duplicate producer is counted as a new family.

Fifty-four image and mutation-control checks pass. Complete Memory 0 images
check sources, receivers, retained unused capacity, result temporaries and
outside sentinels. Empty-result checks observe the live one-byte reservation
inside the producer, one source effect, and unchanged target bytes before the
producer returns. Only that identity byte has no payload value contract.
The full expected image includes the declared global counter change.

The wider-prefix case writes 256 elements, then two elements into the same
receiver. It verifies both count bytes and all retained payload bytes. A valid
one-byte count-store mutant fails when the high byte must be cleared. The data
observer checks the complete array image, a 256-capacity field, its two-byte
count, adjacent scalar fields, retained capacity and owner tops. Valid short,
long, wrong-count, wrong-memory, missing-reservation, missing-restore and early
release modules must fail named assertions.

Eight further failure and mutation-control checks pass. An invalid target
fails before the RHS prints or reserves its result temporary. A division trap
inside a result producer leaves the existing target unchanged. A separate
instrumented native C copy records length 3 and values 1,2,3 at failure at both
optimization levels. Node checks the complete published image and outside
sentinel. The incomplete RHS's private reservation has no value contract.
The terminal failed instance retains that checked reservation and cannot be
started again; host print and snapshot owners are cleared. No exception-unwind
cleanup support is claimed. A valid early-result-landing mutant fails the
protected-image assertion, and a valid inverted-bounds mutant is caught when
it starts the RHS. Wasmtime checks the same intended trap and output order.

The two old assignment-adaptation guard checks now require successful native
and Node execution. The other constructor and frontend-policy checks remain.

The full Wasm suite passes 4,999 checks. The native baseline passes all 18
groups, including 2,782 frontend, 1,367 generated-C and 1,542 TinyCC checks.
All 52 exact shared-backend comparisons pass. All 1,224 unchanged parent O0/O2
Wasm fixture modules are byte-identical, using completed outputs without guest
reruns for the identity comparison. The tested executable matches the frozen
78-file source set and all 5,412 validation inputs. Execution evidence is from
Linux. No timing or measurement lease was used.

## Preserved preparation failure and limits

The first empty-source observer omitted the program's declared global counter
write. The saved module and failure show that `calls` changes from 0 to 1 before
`inside`. The corrected observer models that exact eight-byte write, still
requires the target payload to remain unchanged, and still checks the source
reservation and outside sentinel. The original observer and failed run remain
intact. No production-source change was made for this harness error.

A read-only source search checked captured places, address offsets, dynamic
memory dispatch, zero-byte copies and count stores. It found no confirmed
additional defect. The final matrix includes the identified wider-prefix,
reference-rebinding, temporary-field, reference-element and data-memory paths.

The payload work scales with the active fixed image, not receiver capacity.
The path adds no allocator or persistent compiler state. A pure stored source
uses no new reservation; a value producer uses its existing intrinsic result
reservation. Performance and physical-memory measurements are outside the
correctness-only owner directive.

General nonfixed source-layout conversion, slices, different element layouts
and other nonfixed value consumers remain separate work.

Raw evidence is in `/tmp/goose-wasm-fixed-array-assignment-layout-20261108`.
The [archive manifest](fixed-array-assignment-layout/archive-manifest.json)
records source, executable identity, inputs, commands, failures and final checks.
Binaries and complete generated artifacts remain in the raw directory.
