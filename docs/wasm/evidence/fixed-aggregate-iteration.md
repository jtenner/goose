# Copied fixed aggregate iteration binders

This Stage D increment adds by-value iteration over the admitted Memory 0
fixed/static-capacity limited aggregate arrays. Full backend and performance
acceptance remain open. Parent: `fcaba2e02bc6925f8e9c8c759f82d6eced526d21`.

## Behavior and costs

The storage plan records an `IterationCopy` owner for each checked nominal
copy binder. Its initialization identity is the checked loop node. Existing
bounded layout and frame checks reserve one binder slot per activation.
The binder remains read-only under the frontend's existing copy-binding rules.
Ordinary reference fields retain their original target and access rights.

The array loop retains its existing path capture, reference-slot reload,
current-count check, stride calculation and control targets. After its length
check, it copies exactly one whole element image into the binder before the
body. It uses the existing fresh-owner and copy interfaces with both memories
known as zero. Nested binders have separate slots; repeated passes reuse the
same physical slot after the prior body cleanup. Checked callbacks, defaults,
global initialization, and multiply emitted deferred loops use their checked
node identities. No by-value argument/result ABI is added.

Relative/root/nonfixed types, aggregate values in data memories, slices,
direct field-path iteration and the other pending array operations retain
their guards. Scalar/reference and by-reference iteration use their existing
runtime arm. All new map/plan checks are compiler work.

For N passes and element image D, required byte-copy work is O(N*D), plus the
existing path work. The image includes inactive enum payload and unused nested
limited capacity. One complete binder image is reserved even for a zero-trip
loop or an untaken branch. Frames sum binders; there is no slot reuse across
different binders. Growth retains addressable pages after top restoration.
There is no new per-pass guest heap allocation or stack reservation. Compiler
map entries, emitted code and scratch locals still have costs. The concrete
CPU/RSS/allocation/guest handoff is in `docs/wasm/measurements.md`; it is queued,
not measured. Static bytes/locals and restored logical tops are not speed or
physical-memory evidence.

## Frozen compiler and targeted evidence

The preserved Release compiler is
`/tmp/goose-wasm-aggregate-iteration-20261107/build01/goose-tested`, SHA-256
`c9519e59d47ea996b84d249fee688704bfab0ed49cf5c1ef844e7daf3bdd60d2`.
The source manifest was checked before preservation and subsequent units.
Production source has not changed after that build.

Twelve initial fixture families passed native O0/O2 and reached the exact
parent iteration guard before target acceptance. The candidate then passed
120 emission/validation/Node/Wasmtime/owner commands. Cases include snapshots
after source writes, independent fresh copies, enums and standalone variants,
nested inline fields, empty identities, shallow writable reference targets,
packed data references, captured indices and mutable reference paths, empty
and rebound limited sources, checked callbacks/defaults/globals, repeated
defer emission and normal/early/continue/break cleanup with frame growth.

Three further native-valid fixtures check the loop copy, live inner cleanup
and zero-trip state. A compile-only case proves the binder itself can push a
combined frame beyond memory32; its huge native image is never built or run.
The preserved-compiler controls use a live print completion and owner state,
not sleeps or released addresses. They inspect neighbor bytes, a reserved
zero-trip binder, a live outer data sentinel and inner tops before outer
cleanup can hide a missing restoration.

All 54 commands in controls02 passed. Changed modules first validate, then
fail specific checks: short image copy, wrong stride, source alias instead
of binder, overlong copy, copy before the zero-count branch, omitted inner
restore, and a valid wrong source memory. Guest assertion controls run on
Node and Wasmtime. Host neighbor/zero-trip/live-cleanup controls are Node-only.

## Preserved setup and record corrections

The initial enum fixture used an assignment as an unbraced match arm. Native
parsing rejected it. Only that arm was braced in a separate continuation;
eleven passed native families were reused without rerun. This is a fixture
syntax error, not a compiler repair.

The first live cleanup adapter assumed an eight-byte count prefix. Saved
instructions show a four-byte count: an i64 element uses 12 bytes and the top
is 13 from the initial top of 1; the element starts at offset 5. The original
adapter and failing records are preserved. The corrected adapter reruns only
the failed check on the same guest modules. No production change was needed.

The build unit's native and target scripts initially used the same generic
manifest names. The target script overwrote that manifest after native work;
all individual native command exits/stdout/stderr and the native summary
stdout remain. A log-name proposal was made after the target had already
finished; it is saved as not run, and the executed script was restored.
`native-record-audit.json` reconstructs and checks the eight native statuses
from the unchanged individual logs. It is not an original command manifest.

Raw evidence is under `/tmp/goose-wasm-aggregate-iteration-20261107`.
Each resource unit takes the shared lock nonblocking, waits/reaps all children,
releases it, then verifies owner exit, exact owned processes and a fresh
exclusive probe before handoff. No timing samples are included.

## Full suite and static footprint

The full suite passed 1,034 checks with wasm-tools 1.262.0, Node 24.22.2 and
Wasmtime Python 49.0.0. These include executions, diagnostics and static
controls, not 1,034 independent programs. Fifteen new fixture families are
part of the native/Wasm differential suite.

The static cases keep 13 main-function locals, one eight-byte binder frame
and one loop-copy site at lengths 0/1/32/256 and limited capacities 32/65536,
at both O0/O2. The frame reserve occurs before the loop. The fixed-length
modules are 1,111/1,118/1,358/3,156 bytes; explicit source construction still
grows with the literal. The two sparse-capacity modules are 1,145/1,164 bytes.
Their unused payload is not serialized, but it remains part of the reserved
addressable global image. These are static module/frame/local results only.

The full Linux-native baseline passed with four workers and the explicit
TinyCC library path. Existing device/platform and unsupported JIT skips remain
in the saved log. This does not establish execution on other operating systems
or CPU architectures. All 52 saved C/report/diagnostic/scalar-Wasm comparisons
passed. All 196 prior-module pairs are byte-identical, with matching output,
diagnostics and exits. These results do not measure compiler CPU or guest speed.

## Independent review

The [Astra review](fixed-aggregate-iteration/astra-review.md) found no confirmed
correctness or design defect. It inspected all 40 review files, consulted the
listed parts of all 23 context files, and matched the staged patch, 63 live
files/snapshots, 2,338 archived hashes, 4,622 raw artifact identities and 360
final modules. Its inventory lists unread context ranges. No builds, tests,
timing or source edits ran during review. Source and tests stayed unchanged.

The reviewer independently decoded the twelve footprint modules. Main bodies,
including local declarations, are 213/213/213/215 bytes for fixed lengths
0/1/32/256 and 219/222 bytes for limited capacities 32/65536. These absolute
sizes are not a gain over the parent, which rejected this syntax.

The report keeps record, platform and cost limits explicit. The new fixtures
do not isolate every index width or const/optional/reference-type combination.
There is no new sanitizer or other-platform execution. Performance acceptance
and the queued measurement handoff remain open. No failing valid input was
established by those coverage limits.
