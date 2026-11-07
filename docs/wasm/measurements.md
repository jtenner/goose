# Initial scalar measurements

These results cover the scalar checkpoint only. They do not establish the
performance of multi-memory dispatch, compound values, EH, or workers.

Two separate host windows were explicitly granted by the shared-host
coordinator. Each acquired the global performance lock nonblocking and used
CPU 0, the same two source workloads, two warmups, and seven measured samples.
All children were reaped before each lease release and completion notice.

Host: AMD Ryzen 7 8845HS, Linux x86-64, powersave governor. Runtime: Node
24.22.2 / V8 13.6.233.17-node.63. Native references: GCC 14.2.0, `-O2`.
Compiler: clean Release, GCC `-O3 -DNDEBUG`. Full exact controls and build hashes
are retained with every raw sample.

| Workload | Initial Node run median | Candidate Node run median | Wasm bytes before / after |
| --- | ---: | ---: | ---: |
| Two million integer recurrence steps | 2.047747 ms | 2.048842 ms | 741 / 741 |
| Two hundred thousand wrapping float conversions | 4.736427 ms | 0.270778 ms | 755 / 815 |

The conversion loop's median run time is 94.3% lower for 60 extra bytes.
In-range conversions now stay inside one shared Wasm helper; out-of-range
values and NaN retain the original wrapping fallback. Boundary, f32,
unsigned/narrow, and global-initialization cases pass under both engines.
A test observes zero host conversion callbacks for in-range cases. The helper
is absent when unused. The integer modules are byte-identical; the observed
0.05% median difference is not evidence of an emitter improvement or loss.

The native reference C files and executables for both workloads are
byte-identical between runs. Their process medians were 4.495 / 3.591 ms for
the integer workload and 2.927 / 1.858 ms for conversion. These include process
startup and exit. Node run samples exclude compilation/initialization and
include one captured print. Do not use these numbers as a native/Wasm speed
ratio. Native process variation also shows the limits of these short runs.

Each workload's addressable Memory 0 remained 65,536 bytes. Observed whole-Node
peak RSS was 56,748 / 54,848 KiB for integer and 62,000 / 54,740 KiB for
conversion. These are separate process peaks, not an isolated heap-allocation
measurement or proof of physical linear-memory commitment savings. The
in-range instruction path performs no explicit host BigInt conversion.

Goose invocation observations were 3.916 / 2.940 ms for integer and 4.133 /
3.093 ms for conversion. Each is a single compilation observation, not a
compiler-speed comparison. Node compile-and-init samples include the adapter
and can use V8's module cache. Raw warmups and all samples remain available.

Evidence:

- [Initial samples](evidence/scalar-baseline/samples.json),
  [controls](evidence/scalar-baseline/controls.json),
  [released lease](evidence/scalar-baseline/lease.json).
- [Candidate samples](evidence/scalar-candidate/samples.json),
  [controls](evidence/scalar-candidate/controls.json),
  [released lease](evidence/scalar-candidate/lease.json),
  [exact source patch](evidence/scalar-candidate/candidate-source.patch).
- Harness: `bench/wasm/measure.py` and `bench/wasm/measure.mjs`.

Full generated modules, C sources, native references, and the retained initial
compiler remain under `/tmp/goose-wasm-evidence-upstream/scalar-baseline` and
`/tmp/goose-wasm-evidence-upstream/scalar-candidate`. No further timing was run
under either grant.

## Pending array-copy measurements

The [array-copy stage](evidence/array-copies.md) has functional and static-size
evidence. Its matched accepted modules are unchanged by the two admission
guards. No controlled compiler CPU/RSS/allocation or guest-copy measurements
have been taken. The queued work covers concrete and dynamic identities,
owner count up to the 65-memory limit, payload size, sparse capacity, engine
initialization and high-water retention. It needs matched native/reference
identities, normal host controls and a fresh shared lease. The earlier scalar
grants are closed. No speed or physical-memory improvement is claimed.

## Pending variable-length prefix measurements

The [prefix stage](evidence/varint-prefix.md) has functional and static-size
evidence. Runtime decoding, compiler emission/allocation, initialization and
retention remain unmeasured. The queued cases cover prefix width, memory
identity, owner count and nested paths, with exact native/reference identities
and a fresh shared lease. Prior scalar grants are closed. No speed or physical
memory improvement is established.

## Pending fixed-enum and checked-callback measurements

The [fixed-enum increment](evidence/fixed-enums.md) has functional and static
footprint checks. Its dynamic-source-to-frame helper body is 79/1,133 bytes
for 3/65 memories. Limited-field construction uses 28 locals for both 32 and
256 elements. These results do not measure compiler CPU/RSS, allocations,
guest throughput or retained physical memory. The evidence report gives a
concrete matched-compiler handoff for those costs, including shared struct
callers and checked callback scans. It needs a fresh coordinated lease and
host controls; the scalar timing grants remain closed.

## Pending fixed aggregate-array measurements

The [Memory 0 aggregate-array increment](evidence/fixed-aggregate-arrays.md)
has functional and static-footprint evidence. Compare accepted enum compiler
`25090248` with array compiler `bd3856b6` for shared scalar/reference controls.
For newly admitted programs, compare native C from the same frozen source and
report compiler, engine initialization and guest execution phases separately.
Include named and nested literals at 32/256 elements, explicit COPY wrappers,
sparse limited capacities, exact copies of large unused capacity, enum payload
matches, nested paths, thin/packed references, checked callbacks, repeated
activations and cleanup/frame growth. Record raw samples, source/build/tool
identities, allocation counts, peak RSS, retained pages, Wasm/native-code size
and confidence/qualification limits. The 12/11 constant constructor-local counts
do not establish these costs. This work needs a fresh coordinated scope and
exclusive lease with normal host controls. It is queued, not measured.

## Pending copied aggregate-iteration measurements

The iteration increment reuses one planned frame slot for each fixed aggregate
copy binder. Compare accepted array compiler `bd3856b6` with iteration compiler
`c9519e59` on unchanged scalar/reference loops, constructors, matches, checked
callbacks and defaults. For the new syntax, compare against the parent-accepted
`for &e` plus an explicit fresh `copy(e)` with the same checked output. Record
source/frame differences; the parent cannot compile the new syntax itself.

Separate compiler CPU/wall time, RSS and allocation profiles from instantiation,
initialization and guest execution. Include 0/1/32/256 passes, nested binders,
path depths 1/2/8, thin/packed reference targets, 1/7/16/256/40008-byte elements,
large inactive enum payloads and unused nested limited capacity. Test cold and
warm calls, repeated early exits, defers, live outer owners and growth thresholds.
Record exact source/tool/engine identities, raw samples and qualified uncertainty,
code size, logical tops, addressable pages and separately observed RSS or physical
retention. Copy work grows with selected image bytes; a restored top does not
shrink memory. Constant loop scratch does not prove a speed or memory gain.

Use a fresh coordinated measurement scope with explicit host controls,
affinity, repetitions, warmups and decision limits. If a shared-path change
causes a clear measured loss, park it. No scalar timing grant is reused and no
performance acceptance is claimed by this queued handoff.


## Pending array-place compiler measurements

The [array-place refactor](evidence/array-places.md) retains the accepted source
ABI and byte-identical modules for all 226 current parent pairs. This is not a
compiler CPU, RSS or allocation result. Compare parent compiler `c9519e59`
(commit `b04500bb`) with corrected compiler `5b68b041` from their frozen source
manifests. The private thin-known-memory address correction has failing-first
and passing-after checks in two engines; current source lowering does not emit
that form.

Use matched shared scalar/reference/aggregate controls, constructor sizes
32/256/4096, path depths 1/2/8, concrete and dynamic memory identities,
copies, equality, loops, mutations and print snapshots. Record paired compiler
CPU and wall time, peak RSS, allocation counts/bytes, module/code/helper size,
and locals. Separate cold process costs from warm or cached work. Small value
structs avoid a new heap wrapper but can still add compiler copy and query
work. Restored logical tops do not show released physical memory.

The handoff needs fresh coordinated scope, exact source/tool/build identities,
normal host and affinity controls, declared warmups/repetitions and qualified
uncertainty. Park a clear measured shared-path loss. No scalar grant is reused
and no speed or physical-memory gain is claimed by this queued work.


## Pending canonical reference-ABI measurements

Compare accepted array-place compiler `5b68b041` with canonical reference
compiler `bcc336c9` on frozen matched source. Include thin controls and packed
fixed/static-limited references through direct calls, opaque params, globals,
optionals, stored fields, 1/2/8-step mutable paths, copies, equality, by-value
binders and byte snapshots. Vary owner counts and payload sizes. Record paired
compiler CPU/wall time, allocation counts/bytes, RSS, module/type/local/helper
sizes, engine initialization, guest execution and separate physical-memory
observations. Keep native/reference and engine identities exact.

The 32 focused Node image pairs are identical; 54 of 226 saved module pairs
change; total module size falls by 313 bytes while code sections grow by 405.
Use the corrected completion observer on both compilers. It reads print and
snapshot owners before terminal cleanup; ordinary adapter runs add one optional
terminal-hook check and allocate no callback for it. Neither size result proves a runtime or
memory improvement. Wider params/locals and checked identity dispatch can cost
work even without a new heap wrapper. Use fresh coordinated scope, actual
family/count contracts, exclusive lease and declared host/affinity controls,
repetitions/warmups and qualified decision limits. A clear measured shared-path
loss must be resolved or parked. No scalar grant is reused; performance
acceptance remains open.

## Pending fresh aggregate-data measurements

Use parent `4dc9af87` / compiler `bcc336c9` and final data compiler `12dc79f3`
on matched old supported controls: `wasm_aggregate_array_packed.goose`,
`wasm_struct_refs.goose`, and `wasm_byte_print.goose`. Include known and opaque
prefix paths, scalar/header callers, frame copies and byte snapshots. These
controls compare the shared scratch path with the accepted feature parent.

The parent rejects the new owning aggregate-data form. For that form, compare
the preserved first data compiler `e1eacdff` with `12dc79f3` on the same checked
32/256-row limited-literal, fill/string/default, and unknown-base programs.
Label this as a comparison of two data implementations, not a master speedup.
Include direct and nested named copies, local/global sources and known/opaque
bases at both row counts. Use reviewed compiler `e1bbd1b2` for the named-copy before comparison. It adds four locals
per named source; use its separate failing-first record as the comparison
source, and verify the repaired full images before measuring.
Source, compiler, generated module and adapter identities must be frozen. All
before/after memory models and logical-top checks must pass outside timed spans.

Record paired compiler CPU and wall time, compiler allocation count/bytes and
RSS, module/local/helper sizes, separate engine compilation and initialization,
and guest execution. The ordinary adapter permits one start per instance;
declare any fresh-instance or instrumented-entry protocol before acquisition.
Measure physical commitment separately from addressable pages or restored tops.
Literal work grows with required child initializers and fixed image bytes;
opaque fills/loads/stores may use a bounded memory selector dispatcher.

The static failing-first checks now show 35 known-constructor locals and 15
unknown-base functions at both 32 and 256 rows. They do not qualify CPU, runtime,
RSS or physical-memory costs. Use a new fixed sample/count contract, exclusive
coordinated lease, normal host/affinity checks, declared warmups/repetitions and
qualified uncertainty. Resolve or park a clear measured shared-path loss. No
previous scalar grant or sample budget applies; performance acceptance is open.
