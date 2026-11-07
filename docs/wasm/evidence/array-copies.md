# Same-layout scalar and reference array copies

Fresh-owner construction now accepts an existing admitted array value and
`copy(array)`, with exactly matching storage layouts. Fixed and static-limited
values stay in Memory0. Variable, runtime-limited and growable owners reserve
the complete destination region in their assigned data memory. The source
runs once, and its base and count are captured before destination growth.
Ordinary reference elements retain their referents; the copied owner has
separate storage. Scoped reservations use the existing ordered cleanup actions.
Global destinations retain their reserved storage.

Fixed and static-limited copies use the full static size. Variable and growable
copies use length. Runtime-limited copies preserve capacity and length and use
the full capacity region. Known memory identities emit one `memory.copy` with
concrete source and destination indices. The shared fallback uses nested
`br_table` selection when identities vary. Memory0 sources retain their smaller
existing dispatch. No host copy bridge or guest staging buffer is added.

The independent Astra review found two admission defects. A valid implicit
fixed-to-limited conversion could overwrite the expression type while retaining
the original source storage. The first implementation then used the wrong
copy size and layout. The preserved compiler prints `1,2` where native prints
`3,1`, at O0 and O2 in Node and Wasmtime. The repair checks declared storage or
actual result/element types before it selects a size or emits the source.
Unequal layouts receive the pending-destination diagnostic. This fix adds no
layout adaptation or relocation.

The second finding was an inlined by-value argument binding that became an
ordinary local declaration. The preserved compiler rejects the O0 call but
admits its O2 inline form. The repair checks the binding's existing `inline_arg`
flag before array initialization. By-value arrays remain a diagnostic at both
levels. Both findings have failing-first records. The first reproduction also
preserves an invalid added prefix-width fixture: the native checker required
explicit `copy`. A separate corrected run covers all 11 valid cases at O0/O2.
No setup failure is treated as a production defect.

The final frozen Release compiler SHA256 is `8cf49b9eb51ef6c312cedb1222d32e17f18c6c33bcf659cc4586c3e016bc78b7`.
All 22 O0/O2 admission cases now reject for the specific required reason and
write no module. Four native-valid positive fixtures pass at O0/O2 in Node
24.22.2 and Wasmtime Python 49.0.0, with wasm-tools 1.262.0 validation.
Completed-owner checks verify actual stack tops after `_start`. They cover
separate copies, source preservation, reference identity, capacity, growth,
source effects and temporary storage, indexed/optional sources, global copies,
and return/break/continue/defer cleanup.

The final full suite passed 423 Wasm checks. All 52 older-checkpoint exact
artifact/diagnostic comparisons and 84 immediate-prior Wasm module pairs match.
These 52 comparisons contain 34 native C/report pairs and 18 older Wasm pairs;
they are not 52 new native executions. All eight accepted copy modules also
match the preserved pre-guard compiler byte for byte when compiled at the same
source paths. The guards add no guest instructions in those modules. Paths in
trap messages affect module size, so sizes from different fixture paths are
not optimization comparisons. No fresh full native baseline was run in this
stage: native production lowering did not change, the native fixture oracles
and exact C/report comparisons passed, and the preceding runtime-limited stage
retains its complete native baseline record.

The independent [Astra report](array-copies/astra-review.md) describes the two
findings before repair. Their resolutions are supported by the preserved
[before records](array-copies/reproduce02/before-results.json),
[final exact-reason checks](array-copies/final/admission-results.json), and
[accepted-module comparisons](array-copies/final/positive-equivalence.json).
The final source and harness were frozen before the build; all 4,136 hashes
match. Owner 3857752 exited, all children were reaped, the lease was released,
and the exact-stage process check and fresh exclusive nonblocking lock probe
passed. The probe was immediately released. The [release record](array-copies/release-verification.json)
pins commands, compiler and source provenance.

Raw evidence is `/tmp/goose-wasm-array-copy-20261107`. The initial reviewed
395-check run, both reproduction attempts and final validation have separate
records. Archived `subprocess-records.json` files retain stdout, stderr and
exit files losslessly under their original names; the raw files remain
unchanged in the named directory. No failed attempt or sample is replaced.

The copy cost grows with the number of bytes copied. A sparse runtime-limited
array can still cost its full capacity. The dynamic helper emits M squared
cases for M memories, with the existing bound M <= 65. This is emitted code
size, not a runtime scan. The saved 65-memory test module is 112,340 bytes;
its copy helper body is 78,158 bytes, including local declarations and end.
It also contains other memory helpers. One known identity with one unknown
identity can still use the full fallback. Reachable-pair pruning or a more
specialized helper needs measurement before adding complexity.

Constructor bookkeeping uses a bounded set of locals per copy, independent of
element count. Guest reservation and bulk-copy work grow with payload or
capacity. Compiler vectors, cleanup entries and helper buffers still allocate.
Each data memory begins with one 64 KiB page. Resetting a top permits reuse but
does not shrink a buffer or prove physical release. No controlled runtime or
compiler CPU, RSS, allocation or physical-memory measurements were taken.
The Linux x86-64 functional results do not establish cross-platform runtime
behavior, a speed gain or a minimum memory footprint.

The queued coordinated measurement work covers known and dynamic copy
identities, varying owner count, payload size and sparse capacity, common
compiler paths, engine initialization and high-water retention. It needs exact
native/reference identities and a fresh shared lease. It is part of the full
project's remaining performance matrix, not a reuse of earlier scalar grants.

General layout adaptation, assignments, by-value arguments/results, owned
expression temporaries, compound/relative/pool layouts and relocation remain
pending. This is a bounded extension of the array layout path, not completion
of destination construction or the full Wasm backend.
