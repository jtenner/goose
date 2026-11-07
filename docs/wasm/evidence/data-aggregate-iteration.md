# Copied fixed aggregate binders from data arrays

This Stage D increment extends the existing copied-binder path to ordinary
u32-count data arrays with positive fixed struct, enum or variant elements.
Focused native, Node and Wasmtime checks pass. The integrated Wasm suite passes
1,476 check groups with 80 C++ and 4,262 validation input hashes checked before
and after. The native baseline and all 52 exact comparisons pass; all 242
unchanged parent fixture modules are byte-identical. Independent correctness
review found no production defect and one recursion-coverage gap, corrected
with the actual-call checks described below. This increment does not complete
Stage D or the backend.

## Scope and bounds proof

`ArrayFor` accepts the existing `DataNominalArray` predicate in addition to
inline arrays. It still requires an exact element type, a positive fixed
element layout, and the storage planner's `IterationCopy` origin tied to this
loop. Only inline source arrays require a fixed whole-array layout. A valid
complete data owner has a u32 count followed by that many complete fixed
images. The current unsigned index/count test therefore bounds the whole
selected image. Ordinary references do not gain constructor-origin privileges.

The loop uses the existing captured array walk, current mutable root reload,
checked element address and fixed-copy service. The copy reaches the planned
Memory 0 binder before the body starts. One frame slot belongs to each binder
in an activation. It is not reserved on each pass. Reference fields remain
shallow packed references; source rebinding cannot retarget an existing copy.
Defaults and initializer effects do not run again during the copy.

No layout, reference width, cleanup rule, shared copy interface, allocation
service, compiler field or runtime state changes. Field-path loops, wide or
varint aggregate counts, capacity/growable aggregate owners, nonfixed owning
elements and general by-value aggregate calls/results retain their guards.

## Frozen identities

Accepted parent: `20484f75bf27af082b769da38fff3fea8bdd629c`.
Parent compiler SHA256:
`12dc79f34587854a08bb8c7df44b2866fbc8989962873afb17f8aece2c90dde4`.
Candidate compiler SHA256:
`b60cd4baf028f1c1a3033b3263ca697e17d80a93b2cf2d70567536a866e0ea09`.
The Release build and each completed unit verify the 80 C++ input hashes.
Later test additions use this preserved compiler; no source/binary mismatch is
hidden by rebuilding between fixture corrections.

## Focused behavior and controls

Fifteen source families cover copied snapshots before source mutation,
independent binders, local/global/data reference targets, nullable references,
mixed inline fields, enums and variants, inactive payload bytes, callbacks,
inlined helpers, globals/defaults, mutable root replacement, an effectful index
that grows the outer reference array, zero trips, defers, early returns,
continue, break and live outer owners. Each positive family has a
native behavior reference and the parent's exact copied-binder target
rejection before candidate execution. O0 and O2 are included.

Live derived-module observers read current frame/data tops and complete images
at body checkpoints. Host-seeded unused enum payload and limited-array capacity
bytes prove full-image copying without assuming zeroed storage. Seven validated
damaged-copy forms cover short and long lengths, wrong stride, wrong source
memory, omitted copy, eager zero-trip copy and missing body-top restoration.
Their checks name the intended guest assertion or live-owner failure. A
separate eleven-group admission check preserves field-path, read-only binder
and memory32 frame-size failures. The huge-frame check emits C source only;
it never compiles or executes that source.

## Static footprint and cost limits

Forty count/stride cases cover 0, 1, 32 and 256 rows at strides 1, 7, 16, 256 and
40,008 bytes, at O0/O2. Complete global/frame/data models pass. Each loop has
one stride-sized binder reservation before the loop, one copy site and no
per-pass frame or data reservation. The loop-local vectors stay flat with row
count: 20, 23, 22, 33 and 33 locals for those strides. Each module has eight
defined functions at each count. Source literal construction can still grow
with the number of elements.

For V visited elements of fixed size D, copying does O(V*D) guest byte work.
Existing mutable path resolution can also scale with path depth. Each binder
uses D addressable frame bytes per activation, including recursive activations.
Opaque source identities can dispatch through the existing bounded memory
selector. No new guest heap object, second staging copy or per-pass reserve is
introduced. These facts do not measure compiler allocations, CPU, RSS, engine
runtime or physical commitment. These are historical static facts recorded
before the correctness-only directive. No further performance work is planned
by this thread.

## Preserved observer failure and correction

The first count/stride run completed 32 matrix cases and stopped at the first
large-stride Memory 0 assertion. Its expected snapshot used
`Buffer.from(memory.buffer)`, which aliases the underlying buffer and loses its
old image after growth. This was a test-observer defect, not a compiler defect.
The original observers, failed command, stderr, status and artifacts remain
unchanged. Earlier complete Memory 0 assertions using that view are not counted
as independent image evidence.

The shared test-only `snapshotMemory` helper now copies from a Uint8Array.
Two controls demonstrate that the old view fails after a later write and after
memory growth. The corrected helper passes both. The remaining-only run
hash-verifies and reuses completed native/parent/emitter/Wasmtime artifacts,
runs all 40 corrected Node image models, and repeats the 16 affected live-owner
checks. Seven new native references, eight remaining Wasmtime cases and 59 new
Node processes complete the matrix and observer correction. Original producers
and embedded source paths are retained; the reuse record identifies them.

Raw evidence is under `/tmp/goose-wasm-data-iteration-20261107`.
The pre-directive checks record actual lock acquisition, wrapper bytes and
hash, synchronous completion, child reaping, owner exit, exact-owned process
checks and a successful immediately released exclusive nonblocking probe. The
later native and exact-comparison runs follow the owner's correctness-only
directive: no lease, no timing measurements and no rotation handbacks.

## Integration and native regressions

The integrated suite passes 1,476 check groups in Node and Wasmtime. The native
baseline passes 1,782 parse/roundtrip/typecheck checks, 867 generated-C runs,
1,039 TinyCC runs and all other baseline groups. All 52 older-checkpoint
comparisons pass. All 242 unchanged immediate-parent O0/O2 fixture modules
are byte-identical, with source and module hashes verified. No size report or
performance measurement was run after the owner directive.

The comparison setup initially lacked a Python import and therefore found no
prepared command file. No comparison compiler or guest started in that failed
setup. Its record is retained; the corrected comparison completes normally.

Selected command/status/hash and failure records are preserved in
[data-aggregate-iteration](data-aggregate-iteration/archive-manifest.json).
The [independent correctness review](data-aggregate-iteration/review/report.md)
inspected all 42 primary files in its frozen snapshot and found no confirmed
production defect. Its P2 finding is correct: declaring a function recursive
did not exercise a recursive call. The added regression now keeps copied
binders live across four recursive activations, uses distinct row values and
checks caller data after child return. Native, Node and Wasmtime pass at O0/O2.
A live observer checks the actual Memory 0 top on every enter/exit checkpoint
and after completion. A validated shared-frame mutation fails at the exact
distinct-binder-address assertion in both engines. The initial fixture used
the reserved keyword `guard` as a name; its parse failure is retained and the
valid fixture uses `saved`. No production change was made for R1.

The frozen review predates the later native/comparison results and the owner's
correctness-only directive; its pending statements describe that packet
boundary. The review does not cover the subsequent field-path implementation.
