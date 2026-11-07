# Direct Wasm backend progress

The complete native multi-memory Goose backend is **not finished**. This
checkpoint implements a working direct scalar path and an initial growable scalar-array path. It does not use generated
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
sections, and checked `memory.grow`. Memory 0 frame addresses remain thin. When an array interface is live, ordinary
references use packed i64 addresses; owner-header addresses remain i32 because
all admitted headers reside in Memory 0. Stored owner references retain the
16-byte layout. Known array memories use direct fixed-index loads/stores;
dynamic references use shared checked `br_table` helpers. The backend has an
explicit limit of 64 data memories and rejects a larger valid program before
writing a module. General memory-identity specialization remains pending.

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
- D: use the shared numeric layout authority to implement arrays of all classes, packed/variable aggregates, ADTs, root and
  pool descriptors, relative references, slices, byte views, and serialization.
- E: implement direct nonfixed construction, named-result landing/relocation,
  destination protection, ordered data-stack/defer cleanup, and `try_table` /
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
