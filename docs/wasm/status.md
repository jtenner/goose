# Direct Wasm backend progress

The complete native multi-memory Goose backend is **not finished**. This
checkpoint implements a working direct scalar path and scalar/reference arrays
with fixed, limited, variable and growable layouts. It does not use generated
C as the Wasm compiler's intermediate representation.

Branch: `feat/wasm-multimemory-backend`.
Base: upstream/master `7b90f91d91845f4ef1712e16ed053f395e4e6e1c`, as requested
by the branch-base correction. The original fork-based worktree and local
master were preserved. Implementation commits: `a0dc5c8d` (ABI/baseline), `f3d137b4`
(scalar path), `08acfd56` (warning markers), `cd24b901` (conversion helper), and
`4b260fef` (existing fixture checks). Neither remote nor local master was reset.

## Implemented path

- `src/main.cpp`: `--target wasm`, flag and build forms, frontend/BCE reuse,
  direct binary output, and incompatible native-option diagnostics.
- `src/wasm_binary.h`: bounded module encoding, LEB values, sections, types,
  imports, functions, data, globals, and fixed-memory scalar operations.
- `src/wasm_codegen.h`: scalar integer/bool/float operations, ordinary calls and
  recursion, structured control, scalar globals, checked Memory 0 frames,
  authoritative address-taken storage, scalar references and optionals,
  reference identity/rebinding/return decay, reached scalar defers, and direct
  branches for fully inlined returns, including `return ... from`.
- `src/value_layout.h` and `src/data_stacks.h`: shared concrete layout queries
  and symbolic call bounds. The C backend now uses these extracted services.
- `CMakeLists.txt`: lists the compiler headers. Native runtime sources are
  unchanged. Exact output checks preserve native lowering behavior.

The initial data-stack path adds a separate symbolic storage pass, one physical
memory per overlapping logical stack, a checked bump top for each memory, and
ordered scope restoration. Grow-only and grow-shrink arrays currently accept
explicit scalar or ordinary scalar-reference element literals. Indexing,
iteration, push, pop, clear, length, owner references, and calls through array
references are supported within this subset. By-value array arguments/results,
array temporaries, other constructors, slices, compound elements, and pools
remain target diagnostics.

The emitted modules use Memory32, i32/i64/f32/f64 scalar instructions,
ordinary calls, block/loop/if branches, unaligned loads/stores, global/data
sections, and checked `memory.grow`. Memory 0 frame addresses remain thin. When a growable-array interface is live, ordinary
references use packed i64 addresses; owner-header addresses remain i32 because
all admitted headers reside in Memory 0. Stored owner references retain the
16-byte layout. Known array memories use direct fixed-index loads/stores;
dynamic references use shared checked `br_table` helpers. The backend has an
explicit limit of 64 data memories and rejects a larger valid program before
writing a module. General memory-identity specialization remains pending.

The initial inline layout path now also admits explicit scalar/reference
literals for fixed arrays and static-capacity limited arrays, with packed
prefixes, bounded push/pop/clear, zero-length references and Memory 0 storage.
Large global capacities use zero-filled static reservations. Indexed reference
paths follow native iteration semantics with captured indices and reloaded
reference slots. Value equality now checks lengths and elements; pending operand temporaries
receive destination diagnostics. This extension passed 247 Wasm checks, native
validation, 52 exact comparisons and 56 byte-identical prior Wasm modules. A
nested-type compile-limit regression also passes. An independent
Astra source review found no confirmed defect. See [inline-array evidence](evidence/inline-arrays.md).

The initial variable-array path now admits scalar/reference literals for
`T[]` and fixed-width unsigned length prefixes. Packed values live in assigned
data memories; owner references retain the packed memory/offset address.
Indexing, iteration, length, equality, globals, aliases and reference calls work
within this subset. Large literals use constant constructor scratch rather
than one set of locals per element. Final validation passed 289 Wasm checks,
all native groups across the full run and targeted setup correction, 52 exact
comparisons and 62 byte-identical old modules. An independent Astra review
found no confirmed production defect. See [variable-array evidence](evidence/variable-arrays.md).
Varints, variable elements and general by-value destinations
remain pending. These checks establish module/local-count changes, not a
compiler CPU/RSS or guest throughput result.

Scalar/reference fill literals now work for all admitted array layouts. A
saved fill value runs once even for zero elements; nonempty fills use a loop
and one whole-payload data reservation where needed. Targeted checks include
large dynamic bases and direct variable-owner cleanup exits. This stage passed
301 Wasm checks, 52 exact comparisons and 68 unchanged prior modules. The
independent Astra review found no confirmed defect. See [fill evidence](evidence/array-fills.md)
for exact identities, the earlier native baseline's setup correction and
remaining measurement/coverage limits.

String literals now construct the admitted byte-array layouts, and byte-array
printing preserves per-argument capture, null rendering, whole-line output and
snapshot cleanup on exits. Static byte sources use bulk memory copy; dynamic
memory identities use checked dispatch. The final frozen-adapter run passed
323 checks, with 52 exact older-checkpoint comparisons and 72 unchanged prior
modules. An independent Astra review found no confirmed defect. See
[byte-string evidence](evidence/byte-strings.md) for the preserved adapter-update
overlap, exact provenance, missing measurements and coverage limits.

Runtime-capacity limited arrays `T[..]` now support capacity constructors,
literals, fills, strings, reference calls, indexing, iteration, equality and
bounded push/pop/clear within the scalar/reference subset. Packed capacity and
length offsets are shared with C; data references use packed addresses. The
stage passed 375 Wasm checks, a fresh native baseline, 52 exact comparisons and
76 unchanged prior modules. Independent Astra review found no confirmed defect;
two test expectations were tightened and checked with a valid wrong-field
control. See [runtime-limited evidence](evidence/runtime-limited.md).

Same-layout array copies now construct fresh inline or data owners with bulk
`memory.copy`, including dynamic identity dispatch, runtime capacity, ordinary
reference elements and scoped/global destinations. The independent review
found an adapted-layout check and an inlined by-value admission bypass. Both
were reproduced and repaired with narrow guards. Final validation passed 423
Wasm checks, 52 exact comparisons, 84 prior-module pairs and eight accepted
copy-module pairs. See [array-copy evidence](evidence/array-copies.md) for the
failure records, source identity, review, cost analysis and missing measurements.
General adaptation and protected/by-value destinations remain pending.

Canonical unsigned LEB128 array counts now support `T[varint]` with the
admitted scalar/reference elements. Constructors, exact-layout copies,
indexing, iteration, equality and byte snapshots share the decoded prefix width.
Validation passed 455 Wasm checks, 52 exact comparisons and 92 prior-module
pairs. Independent Astra review found no confirmed defect. See
[varint-prefix evidence](evidence/varint-prefix.md) for the preserved test-wording
correction, exact provenance, costs, gaps and missing measurements. Signed
varint elements and general mixed-layout/slice operations remain pending.

Fresh fixed packed struct owners now use shared bounded layouts and Memory 0
places, with nested admitted fields, exact fresh copies, checked defaults,
scalar field updates, ordinary references and inline scalar/reference array
fields. The repaired final suite passed 590 Wasm checks, the full native baseline,
52 saved exact comparisons, 100 unchanged prior-module pairs and 14 unchanged
earlier struct-module pairs. The new field
literal scratch stays at 22 locals for both 32 and 256 elements. Independent
Astra review found two defects; both were reproduced and repaired with expanded
coverage. See [fixed-struct evidence](evidence/fixed-structs.md) for
exact build identities, preserved failures, evidence-record corrections,
remaining scope and unmeasured costs. This does not complete Stage D.

Fresh fixed enum and standalone variant owners now use shared bounded packed
layouts, exact copies/defaults, field places and statement matches with owned
payload copies. Empty standalone owners keep distinct identities; invalid tags
fail before wildcard/payload access. A reproduced checked-callback scan defect
is repaired with the existing runtime-child walk. The frozen increment passed
744 Wasm checks and the full native baseline, plus 52 exact comparisons.
Of 136 prior-module pairs, 130 are unchanged and six are smaller solely from
the one-source-memory copy helper. Constructor scratch stays at 28 locals for
32/256 elements. Independent Astra review found no confirmed production defect. See
[fixed-enum evidence](evidence/fixed-enums.md) for preserved failures, setup
corrections, exact identities and unmeasured costs. This still does not complete
Stage D or add the general by-value/result ABI.

Fixed and static-capacity limited arrays now admit positive-stride fixed
aggregate elements in Memory 0. Explicit literals, exact fresh copies,
indexed places/references, nested fields and existing by-reference iteration
paths pass the full 904-check Wasm suite. Constructor scratch stays at 12
locals for named elements and 11 for literal elements at 32/256 elements.
The native baseline, 52 exact comparisons and 168 unchanged prior-module pairs
also pass. Independent Astra review found no confirmed production defect.
Data-memory aggregate values, aggregate defaults/fills/mutation, whole-value
operations and the general by-value ABI remain guarded. See
[aggregate-array evidence](evidence/fixed-aggregate-arrays.md) for scope,
controls, exact identity and the queued cost measurements. This is a Stage D
increment, not full backend completion.

By-value iteration over these admitted aggregate arrays now uses a planned,
read-only binder owner. Each selected element is copied before the body while
current source paths/counts and cleanup ordering retain their existing rules.
The increment passed 1,034 Wasm checks, the full native baseline, 52 exact
comparisons and 196 unchanged prior-module pairs. Loop-copy,
alias, stride, zero-trip and live inner-cleanup controls are included. Tested
loop scratch stays at 13 locals with an eight-byte binder slot for the i64
element cases across 0/1/32/256 lengths and 32/65536 capacities. See
[iteration evidence](evidence/fixed-aggregate-iteration.md) for scope, preserved
setup errors, identities and pending performance costs. This does not add
general by-value calls/results, data-memory aggregate values or the other
guarded array operations.
Independent Astra review found no confirmed correctness or design defect;
performance acceptance and the remaining backend stages are still open.

## Host contract

`scripts/run_wasm.mjs` provides versioned print, failure, exit, fmod, and wrapping
float-conversion fallback imports. In-range casts use a shared Wasm helper. It exports the instance's Memory 0 and starts `_start`
once; reentry is rejected. Printing snapshots scalar values before opening the
host buffer, preserving argument effects and avoiding buffers retained by early
returns. The optional `test/wasmtime_host.py` adapter executes the same modules
under Wasmtime. Native C extern/export interfaces require future adapters and
are rejected. No graphics, audio, OS, worker, or queue support is claimed.

## Validation

The unchanged upstream baseline passed before integration. A clean Release
build of the implementation passed the full native baseline suite and 94 Wasm
checks. Wasm checks validate binaries with wasm-tools and compare O0/O2 output
with separately compiled native C under Node and Wasmtime. The suite reuses four existing optional-flow/readonly-reference fixtures.
Checks include integer-width and float stress, optional/identity semantics, cleanup, recursion,
real frame growth, forced growth failure, stable aliases, source preservation,
print resource ownership, unsigned field limits, and multi-memory memargs.

The first post-integration native run found two new fixtures missing warning
markers. The comments were added, and the same complete suite then passed.
No native test was weakened. Audio/gfx/UI/device, transparent-huge-page, Windows
commit-limit, and existing unsupported JIT skips remain in the raw logs.

Exact commands, source hashes, compiler identity, and exits are in
[evidence/release-validation.json](evidence/release-validation.json).
Independent reviews and failing-first regression records are retained under
[evidence](evidence/review-regressions.md). Review findings were checked and
corrected before the final suites. The later shared-service extraction also
passed 52 exact C/stack-report/diagnostic/Wasm comparisons, the native baseline,
and 94 Wasm checks. See [shared-service evidence](evidence/shared-services.md).

The later data-stack Release validation passed 163 Wasm checks and the full
native baseline suite. It independently tests growth failure, all scalar load/store
widths, invalid memory identities, saved-top restoration, separate same-type
owners, stable references across growth, mutable array iteration, reference
elements, and reuse across scopes and element types. The prior 52 exact native
and scalar-Wasm comparisons also passed after the storage implementation.
These results are from Linux x86-64, Node 24.22.2, wasm-tools 1.262.0, and
Wasmtime Python 49.0.0. An independent Astra source review found no confirmed
new defect. Follow-up cleanup checks cover return, break, continue and deferred
allocations at multiple stack bases. See the
[data-stack evidence](evidence/data-stacks.md) for exact identities and limits.

## Measurements

The two initial workloads and converter candidate were measured in separate,
explicitly granted CPU-0 windows, with raw evidence retained. The conversion
median fell from 4.736 ms to 0.271 ms (94.3% lower) for 60 extra Wasm bytes.
The integer-loop module remained byte-identical. These are initial Node
microbenchmarks, not a native/Wasm speed ratio. See
[measurements](measurements.md) for all samples, controls, RSS, compilation
observations, size costs, and limits.

Frames grew addressable Memory 0 from 64 KiB to 128 KiB in the regression test;
this is not an OS physical-commitment measurement. Print ownership tests
observe zero abandoned buffers at each output completion signal. In-range
float casts avoid the host callback; the wrapping fallback still uses a host
BigInt operation for other values.

## Remaining stages and trade-offs

- C: the growable scalar-array subset now has a symbolic storage plan, separate
  memories, checked growth/restores, and dynamic dispatch. Extend the plan to
  protected destinations, temporary owners, and all compound lifetime events.
  General thin-reference propagation remains pending.
- D: scalar/reference arrays now cover fixed, limited, variable and growable
  layouts, including same-layout copies and unsigned LEB count prefixes, plus
  fresh ordinary fixed structs in the admitted field subset. Complete signed
  varint elements, layout adaptations, general aggregate constructors, remaining
  data-memory aggregate arrays and fixed destinations, nonfixed ADTs, root/pool descriptors, relative references, slices,
  byte views, and serialization.
- E: implement direct nonfixed construction, named-result landing/relocation,
  destination protection, cleanup for all remaining value lifetimes, and `try_table` /
  `throw` fallback across remaining nonlocal call boundaries. Engine capability
  probes passed; the backend does not yet emit this fallback.
- F: implement supported native/WASI adapters, OS/program arguments, isolated
  worker instances, global snapshots, typed queues, and worker lifecycle.
- G: implement bounded function/loop memory specialization, dispatch and growth
  hoisting, header/top-load elimination, full differential coverage, and the
  complete dispatch/layout/EH/worker benchmark matrix.

Multiple results, captured out-of-line locals, index/bound types, general
compound values, native interfaces, and remaining nonlocal calls currently
produce target diagnostics. Scalar locals stay in Wasm locals; address-taken
slots use one checked activation region, without intra-frame slot reuse.
Memory 0's exclusive top is limited to UINT32_MAX. Debug overflow checking is
not implemented, and `--debug` is rejected. Wasm recursion uses the engine's
ordinary execution stack. These are explicit limits of this checkpoint.

The shared numeric layout and call-bound services are now extracted. The C
backend still collects lifetime events during emission. The Wasm backend now collects a storage plan before binding the admitted
array owners to memories. That plan must expand with the remaining compound
and destination support. It uses the shared layout authority for sizes.
