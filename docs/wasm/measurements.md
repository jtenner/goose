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
