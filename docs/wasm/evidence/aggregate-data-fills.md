# Fresh fixed-aggregate data fills

Fresh variable arrays of fixed structs, enums and standalone variants now
accept constant-count fill literals. The receiving count prefix can be u8,
u16, u32 or u64. The parent is
`d238b3a64b8d5a052cc48058854cf888260995fb`.

The tested Release compiler SHA256 is
`8a807ab28e4e837c84d99199b015fb3159bd26432c5d43c3d8188f88f3a71f3f`.
Source hashes, compiler flags and the assertion-enabled compiler identity are
retained with the evidence. This work is correctness only.

## Construction and lifetime

`InitAggregateDataArray` checks the nonnegative constant count before
narrowing it to memory32. The existing `ReserveFreshDataArray` checks prefix
range and complete byte extent, reserves the full receiver and registers its
ordered restore. The owner is live before the initializer runs or calls code.
The existing storage plan places any called data owners above it.

The existing `WithFixedTemporary` captures one complete fixed element in
Memory 0. An empty fill still evaluates and captures its value once. A
nonempty fill uses a runtime loop to copy this snapshot into each element.
The snapshot stays live through the entire loop and is then restored. Each
element span is bounded by the complete fresh reservation. Fixed nominal
construction already handles structured exits and cleanup from initializers.

The only compiler change is in one private Wasm constructor function. No new
field, descriptor, table, IR form, ABI or storage-plan rule is added. The
snapshot uses one existing fixed temporary whose size is the element image.
The receiving bytes and copy work grow with element count, as required for
independent values. Generated loop locals do not grow with fill count. No
compiler allocation total, runtime cost or physical-memory result is claimed.

## Failing-first and differential checks

All 43 families pass native execution on the parent, then fail its exact
aggregate-data-fill admission guard. They include zero, three, 128, 255 and
256 elements; every fixed unsigned prefix; packed fields; enums and standalone
variants; references and null optionals; data-memory references; defaults;
nested limited arrays; FP and Boolean values; named snapshots; once-only calls;
real recursion; global owners; caller-live data memories; and return, defer,
break and continue during initialization.

The candidate executes all 43 families at O0/O2 under native code, Node and
Wasmtime, with completed Memory 0/data-owner checks. The assertion-enabled
compiler must emit the same 86 modules as Release and pass Node checks.

The previous u8 aggregate-fill rejection is now covered by positive tests.
Its old guard entry is replaced by a native-valid runtime-capacity aggregate
fill, which still requires the specific compound-element rejection. Aggregate
LEB prefixes remain guarded. Relative/self-relative references and nonfixed
fields remain outside this increment's admission.

## Complete images and validated fault controls

The new observer has 114 checks. At the first checkpoint it poisons the
receiver region and snapshot bytes and writes distinct boundary sentinels.
During the value callback it checks the complete reserved receiver, its count
prefix, the partially written snapshot and the live Memory 0 top. No fill copy
has run at that point. After construction it compares all Memory 0 and data
bytes, including unused free bytes and sentinels, and verifies restoration.

The dynamic case calls the same constructor twice with a caller owner live
for the second call. The receiver must move from the first data memory to the
second while preserving the caller and its poisoned free region. Completed
callee and caller tops are checked separately.

Validated damaged modules omit or repeat value evaluation, shorten or extend
copies, change prefix width or payload offset, use the wrong source address
or memory, force the wrong destination memory identity, omit restores, or
change Memory 0 bytes. Each must fail its specific state or image assertion.
A zero-count fill still requires the value checkpoint and snapshot restore.

## Memory32 count boundaries

A separate eight-check O0/O2 unit checks counts near and above UINT32_MAX.
Each valid program calls a non-inlined function with a false runtime flag, so
the huge-fill body does not execute. The native parent passes all four
programs and rejects their Wasm fill construction. The candidate accepts the
last complete byte extent and passes Node, Wasmtime and completed-owner checks
without running its fill. The first overflowing extent, the NoLocal sentinel
count and a count above UINT32_MAX require their exact compile diagnostics and
no output module. This checks the bound before the count is narrowed.

These checks were added after the original integrated phase. Its runner,
helper and complete input manifest are saved. A source proof requires the
final helper to differ only by the appended count checks and the runner to
differ only by their import and direct call. Every previously executed
statement remains unchanged. The assertion-enabled compiler also checks all
eight count cases against Release output or exact diagnostics.

## Preserved setup errors

Early sketches used C-style field delimiters, missed an enum separator, or
suffered an overly broad syntax replacement. These shared-frontend failures
are preserved and are not compiler defects. Valid native producers were reused
only after their exact source, status and output checks.

The first long-copy control was masked because its source and destination
boundary bytes had the same value. The corrected observer uses distinct
sentinels. All 100 static image checks then passed. The dynamic control builder
next assumed the general copy helper; the actual path uses the existing
`goose.copy_from_frame` specialization. Its parser was corrected against saved
WAT. The 100 static checks were verified and reused for that focused
continuation. No compiler changes were made for either observer error.

The helper-registration setup also assumed an older import format and stopped
before input freezing. The declared assertion build started on unchanged
compiler source. The setup error is recorded; the corrected input freeze and
all source hashes are checked before subsequent tests.

## Final record and limits

All 7,659 correctness checks passed: the integrated phase completed 7,651,
then the separate count-boundary unit completed eight. All 1,892 old fixture
modules are byte-identical to the executed parent modules. All 86 new
assertion-enabled modules match Release, and all eight additional assertion
boundary checks pass. All 52 exact output and diagnostic comparisons pass.
The final verifier checks all 85 compiler source files and 6,055 test/script
inputs.

The [final validation record](aggregate-data-fills/final-validation.json)
contains selected phase results, immutable identities and final counts.
Raw evidence remains under `/tmp/goose-wasm-aggregate-data-fill-20261109`.

This does not add capacity constructors, dynamic fill counts, aggregate LEB
prefixes, nonfixed elements, general nonfixed fields or value calls, slices,
relative references, pools, native adapters or worker compilation. The full
backend remains incomplete. Stage F scope remains an owner question.
