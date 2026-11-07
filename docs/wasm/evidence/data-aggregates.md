# Fresh fixed aggregates in data arrays

Targeted behavior, reservation, and footprint checks pass. The full Wasm suite
passes 1,251 check groups on the repaired compiler, with 80 C++ and 4,223
validation input hashes checked before and after. Independent review found no
confirmed correctness defect and one avoidable copy-local growth path. The
narrow repair, expanded suite, repaired-compiler native baseline and final
52 exact compatibility comparisons pass. Earlier native execution groups and
warning-only/exact compatibility checks passed on the reviewed compiler.
Performance acceptance is open. This increment does not complete Stage D.

## Scope and proof

The first slice admits variable arrays with the ordinary u32 count and a
positive fixed struct, enum, or variant stride. Fresh explicit literals and
exact-layout whole-array copies use the existing logical data stacks. Ordinary
references keep their canonical packed memory/offset representation. Fixed
inline fields can now live in the same nonzero data memory as their containing
row. No language layout, stored reference width, or header ABI changes.

A declaration must have its checked owner and storage assignment before it can
obtain a fresh data destination. The factory checks the full count/stride byte
size, reserves the entire owner image, and registers cleanup before the first
prefix or child store. Child literal ordinals and nested field offsets must fit
that owner extent. A runtime-count copy cannot obtain a literal child token.
The factory retains the actual memory identity and saved top; each child does
not allocate another logical stack or cleanup record.

The exact-copy path captures the source view and count before reserve. It
requires the same stored layout, preserves shallow reference semantics, and
uses the existing checked copy service for the actual source and destination
memories. The storage plan keeps initializer callees above the live destination.
Early return from a partial initializer can therefore restore the saved top.

Only fresh reserved child arrays carry the constructor origin used to form
prefix addresses without a separate helper per constant row offset. Their full
reserved span proves that the addition cannot carry into the packed memory id.
Ordinary borrowed references retain the existing checked offset behavior.
Concrete fills remain direct instructions. An opaque zero fill uses one cached
selector dispatcher, bounded by the backend's existing memory limit.

Wide/varint aggregate counts, aggregate fills and capacity constructors,
zero-stride elements, owning nonfixed fields, data by-value iteration,
whole-value replacement, by-value arguments/results, adaptation, general
aggregate equality/rendering, pools and relative layouts remain guarded.
By-reference root-array iteration and the existing field/reference consumers
can use the new owners. Field-path loop admission is unchanged.

## Frozen identities

Accepted parent: `4dc9af871426b6f440f5bdbe7f009531f4d72600`.
Parent compiler SHA256:
`bcc336c9f3f06f604b6ecdb002f4f355dae24bca9691e5d1b16ca30dfef7148c`.

First tested data compiler, before footprint repairs:
`e1eacdffc85c2f042b72127579ea332a5426384e373478b571c859f98c87ea42`.
Reviewed data compiler:
`e1bbd1b28d51382014fe34c1cf93dfff039164286fdb6718f1e27b521b65905c`.
Named-copy repair compiler (build06):
`12dc79f34587854a08bb8c7df44b2866fbc8989962873afb17f8aece2c90dde4`.
The current build verifies all 80 C++ input hashes. Only Wasm code changed
between these data compiler sources; native reference results were reused only
with source, executable, status, output, and artifact hash checks.

## Behavior and failure controls

Initial checks cover row fields and references, independent copies, nested
inline arrays and enums, global owners, default zeros, inline strings, fill
values evaluated once, and functions entered at different logical stack bases.
Six original cases pass Node and Wasmtime. All saved before/after full images
match after the footprint repairs.

The separate qualification has 34 declared guest outcomes: six healthy native
references, twelve healthy engine cases, eight reservation controls, two valid
wrong-memory-zero controls, and six valid reordered-constructor controls.
A dirty destination makes missing or wrong-memory zeroing observable. Both
engines reject the damaged zero fill at the designated source assertion.
A poisoned copy count and a real hard-limit growth failure leave the saved tops
and complete pre-operation memory bytes unchanged, before any child call.

The effect trace detects order changes even though all stored call results are
equal. It includes nested inline constructors that use the same scratch bank,
zero-count fill evaluation, a return from an unfinished initializer, a copied
frame value, defers, continue, break, repeated calls, and a live outer owner.
The owner checks wait for actual guest completion and read the exported test
tops. They do not infer release from old object bytes or unchanged page counts.

New permanent fixtures also cover nonzero inline-byte argument capture before
later mutation, optionals, booleans, f32 rounding, signed zero, f64 and NaN.
They pass the final integrated Node/Wasmtime suite. The owner observer reads
actual print/snapshot counts before terminal cleanup; a separate derived-module
check reads the current stack tops after guest completion.

## Footprint evidence and cost limits

The first implementation failed its explicit scaling assertions after every
native/engine/full-image behavior check passed. Limited-field literals grew
from 318 to 2,334 locals for 32 to 256 rows at both optimization settings.
Unknown-base constructors grew from 79 to 527 functions. Original records and
the original executable remain separate from the repaired runs.

Per-function prefix and constructor scratch caches now keep limited-field
constructors at 35 locals for both row counts. Fill/string/default constructors
remain at 55. Unknown-base cases have 68 maximum locals and 15 functions at both
sizes. The same assertions pass and all before/after images match. At 256 rows,
the known limited module falls from 236,677 to 227,834 bytes; the unknown-base
module falls from 347,161 to 290,034 bytes. These are static artifact results.
Literal code still grows with the number of required initializer operations.

The new tokens are emission-local values. Scratch caches are fixed per function
and Wasm value type. No runtime owner wrapper, heap, per-child data reservation,
or additional staging copy is introduced. Existing helper creation can allocate
compiler objects, and opaque selectors can add guest dispatch. Compiler CPU,
allocations, RSS, engine initialization/runtime and physical memory have not
been measured for acceptance. Flat local/function counts are not those costs.
The [matched-source measurement handoff](../measurements.md#pending-fresh-aggregate-data-measurements)
remains required before performance acceptance; no old scalar window or sample budget is reused.

## Preserved setup and policy failures

Initial native preflights rejected a stored reference inside a declared recursive
cycle, a zero-length struct field, and a missing explicit narrowing cast. Each
source/error is preserved. The final fixtures use a reference-free out-of-line
row, an empty limited field, and explicit casts. Passed parent rows were reused
without rerunning them.

Initial full-suite attempts stopped at old private policy assertions and old
struct/enum negative controls that still rejected the newly admitted ordinary
data form. The corrected tests accept the intended form and enforce exact
reasons for the remaining wide/varint, growable, and zero-stride limits. No
production compiler change was made for those test corrections.

Raw records are under `/tmp/goose-wasm-data-aggregates-20261107`. Completed units
have child/reaping, owner-exit and fresh exclusive-probe records. New wrappers
also record actual acquisition and an exact wrapper snapshot/hash. One busy
nonblocking acquisition started no child and is recorded as a deferral.

## Native continuation status

The native baseline completed all generated-C checks (852), TinyCC checks
(1,024), and the other execution/diagnostic groups. Its exit was 1 because two
new fixtures lacked three expected-warning comments. The failure output and
original fixture bytes are retained. The repair adds only leading comments;
removing exactly those bytes reproduces the failed sources and their hashes.
No compiler rebuild or guest behavior change is involved.

The first short warning helper then stopped after the compiler exited 0 and
warning matching passed: the helper required phase-summary output but omitted
`--stats`. That failed helper is retained unchanged. A separate continuation
uses the native suite's phase-output option and warning matcher. All four O0/O2
parse/roundtrip/typecheck checks pass with exact warning-marker matching. The
52 older-checkpoint exact comparisons also pass. Passed native execution groups
were not rerun for comment or helper changes.

## Saved-module compatibility and provenance

Final repaired-compiler checks retain 234 immediate-parent O0/O2 module pairs from unchanged accepted-parent
fixtures. Of these, 162 are byte-identical and 72 change. Total module and code
section size both fall by 1,031 bytes; total declared locals fall by 421, and
the total defined-function count is unchanged. These are sums across test
artifacts, not per-program performance or physical-memory measurements.

The before/after full-suite identities cover 80 C++ files and 4,222 validation
inputs. The current compiler was not rebuilt after comment-only warning fixes;
the continuation records both hashes and verifies the exact added comment
bytes. The build05 scaling script imported the local-count parser from
`test/wasm_backend.py` without naming it in that unit's primary input manifest.
A separate parser-provenance record verifies its bytes against the earlier
frozen validation manifest and accepted Git source. This omission and the
companion check remain explicit. The reconstructed first-data C++ snapshot is
labeled retrospective and matches its original 80-file build manifest.

Selected commands, hashes, statuses, logs and failure records are archived in
[data-aggregates](data-aggregates/archive-manifest.json). Large binaries and
memory images remain at the recorded raw paths with their existing identity
records. Archive inclusion and hashes are checked against the staged Git index.

## Independent review and named-copy repair

The independent Astra review inspected all 37 main files and verified the
frozen patch, input and executable hashes. It found no confirmed semantic
correctness defect. Its P2 cost finding identifies a named fixed source in
each fresh data row: resolving its frame address adds one local, then the
shared fixed-copy path adds three more. The earlier literal/default/fill
scaling families did not exercise that copy path.

A separate frozen-compiler check now proves the finding. All 32 native,
32 Node and 32 Wasmtime runs pass full behavior and independent data-memory
models. Direct and nested names, local and global sources, known and dynamic
bases, and O0/O2 are included. All sixteen 32/256-row family pairs then fail
the local-count assertion: each added row costs four locals, or 896 locals
for 224 added rows. The original source, binaries, records and intentional
failure remain intact.

The repair is limited to named same-layout nominal values inside a proved
fresh data destination. It uses the existing direct frame/global copy service
with the constant checked image size, as the fixed-array constructor already
does. Empty images retain their existing identity handling. Ordinary borrowed
sources, frame-only constructors, shared fixed-copy lowering and admission
remain unchanged. The regression is now part of the permanent suite. All sixteen family pairs
have flat local vectors, with at most 36 locals. All 32 native, 32 Node and
32 Wasmtime cases pass. Node provides the complete independent data images;
Wasmtime provides output and guest-assertion coverage. The integrated suite
passes 1,251 check groups, including execution of fill at every one of the 65
admitted memory identities, plus bounds and invalid-selector controls.

The first before/after Memory 0 comparison had different source paths. One
matched-path continuation then still failed exact bytes: removing redundant
address checks also removes repeated diagnostic filename strings and relocates
the frame start. These are legitimate image-layout changes, not equal-image
claims. Both original assertions remain failures in their own records. A
saved-file parser checks all 64 complete Memory 0 images against each module's
declared static data (zero prefix, exact diagnostic filenames and exact output
literal), plus the independent expected template bytes at the global address
or initial frame top. All pass. All 48 complete data-memory image pairs are
byte-identical and match the independent data models. No extra guest rerun is
used for this parser. Its first one-segment assumption failed on the explicit
global-reservation gap; the corrected model handles both declared segments.

One exact-source/path 32-row example falls from 159 to 31 locals, 3,620 to
1,333 code bytes and 8,077 to 2,974 module bytes. These are static costs only.
The independent review covered the frozen pre-repair patch. The ten-line narrow
repair has the separate failing-first and passing evidence above; no second
independent review is claimed.

## Final repaired-compiler native and harness checks

The final repaired compiler passes the complete native baseline with the
explicit TinyCC library path: 1,752 parse/roundtrip/typecheck checks, 852
O0/O2 generated-C checks, 1,024 TinyCC runs and all other baseline groups.
Existing unsupported-platform/layer/JIT skips remain in the retained output.
The earlier exit-1 warning-marker baseline is not relabeled as a pass.

Four filesystem-only controls also prove a test-harness issue: the new named
scaling helper fails before reaching its emitter if its artifact directory
already exists. Adding `exist_ok=True` permits both fresh and existing output.
The in-memory fixed helper bytes match the later source edit exactly. No
compiler or guest ran inside these controls. This one option changed after
the passing 1,251-group suite; guest source generation, compiler C++ inputs and
assertions are unchanged. Its companion provenance and final input manifest
make that boundary explicit; no additional full-suite replay is claimed.

One attempted final native acquisition returned 75 before any child or lease
file because Slipstream's combined cost/screen unit still held the lock. An
acquisition message was sent before its result was checked and was corrected.
The kernel holder was read without interruption; no Goose overlap occurred.
The separate native-baseline03 ran only after actual verified peer release.
