# Newly arrived Goose capabilities for Slipstream

Survey requested 2026-10-31; researched 2026-11-01. The best immediate candidates are **root structs for state ownership** and **`move_from` for existing copy loops**. Pools are useful building blocks for new storage designs, but do not replace Slipstream's collector or its resource accounting.

## Scope and evidence

This surveys the 118 upstream commits in `64d62fc7..40369bd1`, using the requested rebased fork snapshot **`4abab61546ca4e7266005fc3a1cadb35618ab99c`** for all Goose file/line references. The commit list, functional documentation changes, relevant implementation diffs, and regression fixtures were inspected. There is **no CHANGELOG file in that tree or changed in this delta**; the commit history and changes to `docs/reference.md`, `docs/stdlib.md`, `docs/packages.md`, `docs/goose_spec.md`, `docs/implementation.md`, and design/testing documentation supply the change record.

Slipstream is available at `/home/dev/Projects/slipstream`, HEAD **`781e53d2e10ebe8d9ac415c350f25081c6127b1b`**. Its source was inspected read-only. Existing changes to `experiment.md` and untracked `experiment-results.md` were left alone and were not evidence for these conclusions. Slipstream references below are relative to that repository; Goose references are relative to this repository. Line numbers refer to these snapshots, not future master.

A source search over Slipstream's Goose and build files found no declarations/imports or calls using `root struct`, `slot_pool`, `slice_pool`, `binary`, `c_headers`, `move_from`, `range_index`, or `check_length`, and no extern growable-array parameters. This establishes absence of direct adoption in the inspected source, not absence of transitive compiler/runtime benefits. The fork already contains the upstream implementations, samples and tests; those are not independent adoption by Slipstream. Editor usage and the version of existing executables cannot be inferred from source.

Ratings concern implementation payoff: **PROVEN** means a concrete existing source pattern that the capability directly simplifies; it does not mean a migration or speedup was tested. **PLAUSIBLE** means a clear fit with unmeasured pain or integration cost. **SPECULATIVE** means a conditional future use. No compilation, benchmarks, code changes, publication or build artifacts were needed; the only deliverable change is this survey.

## Ranked opportunities

### 1. Root structs own several independent arrays — PROVEN

**New capability.** One local/global owner can hold several independently growing fields, with one lifetime and references passed to helpers. This removes the ordinary struct's single-resizable-tail restriction. Commits `a01815f7`, `9e427c33`, `683ebc94`, `d096b132`, `6b4d3c34`, `e2923724`, `7c41c58a`, with published contract `cbc64a32`. Evidence: Goose `docs/reference.md:1344` (Root structs), `docs/goose_spec.md` §3.4; the component allocation is implemented in `src/codegen_stmts.h` (`BindLocal`).

**Current use and target.** Not adopted. Slipstream `gc/heap.goose:14–55` separately declares more than twenty backing arrays and wires them into `Collector`; `src/model.goose:50` does the same through `Module` references; `src/stack.goose:33` through `Machine`; `src/amd64.goose:13` through `Writer`; `src/redline_ir.goose:40–69` through analysis/SSA/function contexts. A local root owner can absorb backing-array declarations and much of this constructor wiring while helpers continue to borrow it. The clearest first target is a small compiler writer or optimizer workspace, followed by collector state once its budget calculations are preserved.

**Limits.** No nested owners, owner arrays, by-value returns, whole-owner serialization, public C layout, or worker transfer. Keep ordinary packed ABI records and independently scoped child owners. Existing callback scopes may still be needed to bound lifetimes. Roots do not loosen the fork's shared-memory rules.

The companion `56bbde07` extends compact links and checked index types to **direct mutable grow-only fields of global roots**, e.g. `u32 in pool.items` (`docs/reference.md:1395`, `docs/stdlib.md:702`). This is a genuine additional language capability, but its Slipstream fit is **SPECULATIVE**: the inspected contexts are predominantly local/per-instance and must not become globals merely to obtain named index types.

### 2. Checked overlap-safe slice copying — PROVEN

**New capability.** `dst.move_from(src)` checks equal lengths and copies fixed-size, copyable elements with memmove semantics; it does not clear the source. Commit `d24161f4`; Goose `docs/reference.md:907–936`, `src/codegen_builtins.h:251` (emits `memmove`).

**Current use and target.** Not adopted. Slipstream `gc/heap.goose:555` copies collector bytes in a loop; `src/redline.goose:23–30` copies chunks into the output buffer element by element. Equal-length byte slices express both directly. This removes hand-written indexing, with overlap safety useful for future optimizer buffer edits. The collector currently documents nonoverlapping relocation, so do not claim it has an overlap bug.

**Limits.** Preserve admission/bounds checks and chunk flushing. Self-relative elements cannot be copied this way, and raw native addresses/shared capabilities are not ordinary slices. Actual throughput versus the existing optimized loops is unmeasured.

### 3. Complete fixed-width binary readers — PLAUSIBLE

**New capability.** Checked signed/unsigned 8/16/32/64-bit reads, both byte orders for multibyte values, and bit-preserving f32/f64 reads; offset and cursor forms. Before `23a7533b`, the module only provided u16/i16/u32 little-endian numeric reads. Evidence: Goose `docs/stdlib.md:1029–1085`, `stdlib/binary.goose:30–100` and `:128–199`; float reconstruction uses `memcpy` in `src/runtime/runtime_ext.h:67`.

**Current use and target.** No `binary` import. Slipstream `src/redline_immediates.goose:30` assembles fixed-width immediate bits byte by byte. The new u32/u64 readers can simplify a contiguous-buffer fast path for optimizer and compiler decoding; float readers suit host-boundary decoding that actually wants float values. Preserve integer bits where the optimizer tracks literal representation.

**Limits.** This is not a streaming or LEB128 decoder. Slipstream `src/reader.goose:7–28` tracks refill boundaries, absolute limits and other state. Keep its refill/diagnostic/accounting behavior and three-byte-buffer tests; use a fallback or at most a small fixed-width scratch buffer across boundaries. Never restore whole-module buffering. Big-endian formats are a future host-format use, not a Wasm decoding need.

### 4. Package-owned C adapter headers — PLAUSIBLE

**New capability.** A program/package sidecar can set `c_headers`, including platform suffixes. Headers appear after generated Goose types and before extern declarations/function bodies, enabling `static inline` adapters without a separate C object or per-command `--include`. Commit `6ac5828c`; explanatory examples `2ed1a63d`. Evidence: Goose `docs/packages.md:175–196` and `:258–330`, plus `src/packages.h` (`LoadSidecar`) and `src/main.cpp` (appending `pkg.cheaders`).

**Current use and target.** No `c_headers`. Slipstream `src/run.build:1` lists native assembly sources. This would make future small native/host adapters package-local and let them consume the actual generated packed types. It also simplifies fork-side native interop regression fixtures.

**Limits.** Existing `--include` already enabled this placement; the new part is package integration. This is not automatic C-struct import or a stable ABI guarantee. Separately compiled sources cannot see those generated declarations; package `c_flags`, `c_include` and `c_defines` do not apply to the generated translation unit. Retain Slipstream's direct-syscall assembly file adapter; adding C file I/O would contradict its instructions.

### 5. Reusable contiguous slices as a library owner — PLAUSIBLE

**New capability.** `slice_pool<T>` bundles storage and free-span management, with allocate/free/resize, direct `alloc_copy`, and `recycle_all`. Commits `fa1b1640`, `17c512ef`, `2bbc8f34`; current runtime-backed span tree `93f1ad0a`. Evidence: Goose `docs/stdlib.md:710–791`, `stdlib/slice_pool.goose:9–94`, `stdlib/slice_pool_internal.goose:12–15`.

**Current use and target.** Not adopted, nor is legacy `reusable[]` used in the inspected Slipstream source. Plausible for optimizer per-node variable runs and reusable compiler scratch, where `Types { pos, len }` currently describes ranges (`src/model.goose:5`, `src/redline_ir.goose:64`). `alloc_copy` avoids allocate/default-fill/overwrite scaffolding; `recycle_all` retains initialized storage between phases.

**Limits.** Current append-only ranges may be simpler and cheaper; adopt only where independent reclamation is needed. Relocation returns a new view without retargeting old views. There is no occupancy/double-free protection, high-water storage remains retained, and allocator metadata is not a public persistence format. This is not a replacement for collector page placement, moving-GC semantics or budget admission. Upstream Windows measurements still show backend/workload gaps (`bench/slice_pool.md:14–32`); they do not predict Linux Slipstream performance.

### 6. Reusable slots with destination-aware builders — PLAUSIBLE

**New capability.** `slot_pool<T>` offers fixed-size slots, LIFO reuse, direct reference/index allocation, `alloc_with`/`alloc_index_with` for construction at the final address, `free_ref`, and `recycle_all`. Commits `71ca3687`, `0e34d3a7`, `0356ddae`. Evidence: Goose `docs/stdlib.md:608–708`, `stdlib/slot_pool.goose:6–69`. Pool references can be stored/returned/captured under ordinary lifetime rules, unlike the restricted legacy builtin pool-reference mechanism.

**Current use and target.** Not adopted. A fit for new mutable optimizer graphs or independently retired compiler metadata; builders support self-relative links without constructing an illegal temporary copy. Slipstream's existing optimizer nodes use u32 indices and removal flags (`src/redline_ir.goose`), so replacing them is a design decision, not a proven cleanup.

**Limits.** No generation counters, occupancy tracking, tracing, reference counts or automatic destruction. Freed references can observe replacements. Collector `GcRootToken`/`GcHostRef` explicitly carry domain/generation identity (`gc/model.goose:92–94`), which a slot pool does not replace. Keep stable node IDs where analyses depend on them. Whole root owners cannot be sent to workers.

### 7. Native functions can fill typed growable arrays — PLAUSIBLE

**New capability.** `extern fn` accepts `T[>..]&` for any flat fixed-size `T`, extending the former byte-builder-only allowance. Hidden inside the pool-runtime commit `93f1ad0a`: `src/typecheck_calls.h` changes `ExternParamOk` from `IsU8` to `ExternValueOk`; Goose `src/runtime/goose.h:1–10` documents the contract; `docs/reference.md` §23 and `docs/packages.md:237` describe it.

**Current use and target.** No extern growable-array parameter found in Slipstream. A future native adapter could append typed relocation/metadata records directly instead of building bytes or returning a separate native allocation, useful for host boundaries and compiler backend helpers. `slice_pool_internal.goose:12` is an actual upstream user of a struct-element builder.

**Limits.** C must respect packed element size, initialization, stack top/header count, capacity and borrow lifetime. `gs_bld_append` remains a byte helper, not a new generic append routine. This does not permit native code to retain the borrowed builder or share it across threads. Avoid introducing native helpers where ordinary Goose already suffices.

### 8. Reset borrowed fields before reusing their buffer — PLAUSIBLE

**Unlocked pattern, retained under the brief's fix exception.** Assigning static data such as `""`, rebinding an optional reference to null, or resetting a holder to a literal with such defaults now proves that the holder no longer borrows shrinkable storage. A helper can clear those fields, shrink/refill its buffer, and repopulate the views on repeated calls. Commit `0357b1c2`; Goose `docs/implementation.md:2298`, `test/lifetimes/emptied_static_fields.goose:14–30`, with negative path/other-field fixtures.

**Current use and target.** No demonstrated occurrence of that exact repeated reset/shrink pattern in Slipstream was established. It is a clear fit for future reusable host-message/parser view objects or optimizer scratch views, without extra scopes to appease stale holder facts. Existing streaming reader policy explicitly avoids retaining metadata pointers into input (`src/reader.goose:7–8`); preserve that policy.

**Limits.** Every relevant path/field must release the borrow. Assigning another dynamic slice is not a release, and this is a lifetime-analysis improvement, not shared-memory release or deallocation.

### 9. Checked slice provenance and allocation counts — PLAUSIBLE

**New capability.** `array.range_index(slice)` recovers a contained slice's index even when origin is only known at runtime; `array.check_length(n)` validates an element count against the data-stack reservation before mutation. Commit `d6a3ceaa`; optional literal failure messages added by `52282722`. Goose `docs/reference.md:913–929`, `src/codegen_builtins.h:462–497`.

**Current use and target.** No calls found. Useful for a future Goose-side arena/free API receiving slices from helpers, or fork-side safe container libraries: delegate containment/alignment and count representability checks to the language instead of pointer arithmetic. Slice pools already use these internally.

**Limits.** Empty slices from any origin return index zero. Containment does not prove a live allocation or prevent double frees. `check_length` does not reserve memory, check remaining stack space, or enforce Slipstream's application budget; retain its collector and validator admission checks (`gc/heap.goose:15–30`). Neither operation handles raw-memory capabilities.

### 10. Stable generated C across host C++ compilers — PLAUSIBLE

**Unlocked workflow.** `2c7d8d5a` explicitly sequences code-emitting expressions instead of relying on C++ argument evaluation order. Goose `src/codegen.h:1548` sequences signature emission; `test/emit_order.py:1` guards emission ordering. This is included as a fix that makes cross-toolchain byte-for-byte generated-C comparisons practical, not a new language feature.

**Current use and target.** Automatic when compiling with this compiler source; no opt-in. Slipstream's Makefile uses `goose++ build`, but existing binary provenance and a cross-host C comparison workflow were not established. Clear payoff for fork regression triage and build-reproducibility investigations: fewer irrelevant generated-source differences.

**Limits.** Does not promise identical binaries, source paths, target-dependent output or all compiler configurations. Upstream's reported corpus comparison is their evidence, not a measurement performed here.

### 11. Standard-library failures point to the caller — PLAUSIBLE

**New diagnostic capability.** Runtime checks/aborts inside stdlib report the application's initiating call, including nested library calls; generic stdlib type errors are anchored at the instantiating user call. Commits `52282722`, `2b509397`. Goose `docs/reference.md:3069`, `src/codegen.h:224–249`, `src/typecheck.h:592–603`.

**Current use and target.** Automatic for relevant builds; Slipstream already imports `std` and `os` (`src/reader.goose:2–3`, `gc/heap.goose:2`). Helps validator/collector/library integration debugging and fork bug reports. No source migration needed. The exact compiler used for existing executables is unknown.

**Limits.** This is diagnostic attribution, not recovery or a replacement for Wasm-specific offset/error messages; it does not automatically give arbitrary application helper libraries the stdlib treatment.

### 12. Safe in-place construction of call-valued relative fields — SPECULATIVE

**Unlocked pattern.** `78744fda` fixes pushed literals whose fixed-size relative-reference-bearing field is produced by a call/conditional/block: construction now occurs at the destination instead of copying a temporary with invalid offsets. Goose `src/codegen_construct.h:1002–1013`, `test/codegen/pushed_literal_call_fields.goose:11–16`.

**Current use and target.** No matching Slipstream use was established; current optimizer structures use explicit indices. A future compact linked-node representation can use small field factories, improving compiler/optimizer construction code. Included only because the pattern previously generated corrupt links, not because ordinary bug fixes are survey scope.

### 13. Hosted embedded JIT and conditional SELinux support — SPECULATIVE

**New operational capability.** `cce94b91` binds embedded TinyCC output to a runtime compiled into Goose, avoiding recompiling most runtime code or needing system SDK headers for ordinary JIT programs. It also introduces the CMake packaging setting `GOOSE_TCC_LIB_PATH`. `00329a57` enables `CONFIG_SELINUX` when configuring on Linux with `/sys/fs/selinux/enforce`, selecting separate writable/executable mappings. Goose `docs/design/jit_backend.md:33–83`, `src/jit_runtime.c:1`, `cmake/libtcc.cmake:60–63`.

**Current use and target.** Not evidenced in Slipstream's native `build` workflow. Potentially useful for quick single-threaded Goose fork reproductions or deployment on appropriately configured SELinux hosts. This is Goose's embedded C JIT, not Slipstream's Wasm machine-code backend.

**Limits.** No worker/TLS support is thereby added to TinyCC; fork shared memory/UnsafePtr remain native-only. Arbitrary included C headers and constructor/destructor/atexit hooks still have limitations. SELinux detection is at compiler configure time, not an unconditional portable property of all binaries.

### 14. Generic UFCS completion — PLAUSIBLE

**New tooling capability.** Completion matches generic struct/enum instantiations to eligible first parameters, shows instantiated field types, and labels roots correctly. `5b0fdc61`; Goose `src/lsp_features.h:1871–1894` and `:1962`, `test/lsp/pools.goose`.

**Current use and target.** Personal editor usage is unknown. Useful when introducing generic pools/workspaces, and for fork library authoring; it makes applicable methods discoverable. No execution semantics or new method-call syntax.

### 15. Searchable documentation site — PLAUSIBLE

**New tooling capability.** Section-level documentation index plus browser-side fuzzy search. `3cc84860`; Goose `docs/site/generate_search.py:44–90`, `docs/site/search.js:1–17` and `:51`, `docs/site/build.py` integration.

**Current use and target.** No evidence of personal usage; developer aid for finding lifetime, native ABI and pool contracts during Slipstream or fork work. The index is for the generated documentation site, not a new runtime search container, compiler symbol index or language builtin.

### 16. Automatic alignment of declaration groups — PLAUSIBLE

**New formatting capability.** `8f528987` aligns types and equals signs in consecutive compatible declaration rows. Goose `src/format.h:334–343` and `:545–570`, `test/format.py` golden cases. Existing `goose format` gains behavior; no new command is introduced.

**Current use and target.** No formatter invocation found in the inspected Slipstream Makefile. Could reduce manual layout work in collector/ABI record definitions and fork library code. This is low-payoff presentation work; do not combine a mass reformat with a behavioral migration.

## Strong-looking features that do not fit, or are not shipped features

- Whole-root worker transfer: explicitly unsupported; use worker-local owners, not roots as substitutes for the fork's shared capabilities.
- Named global-root index types: useful in single-owner libraries, but a poor default for Slipstream's per-instance or parallel state.
- `slot_pool` as a collector: lacks tracing, generations, domain identity, moving-object handling and application budgets.
- `slice_pool` as universal memory reclamation: high-water storage persists, and old views do not follow relocated runs.
- Big-endian binary reads: useful for other external formats, not Wasm's little-endian fixed-width constants; neither endian API parses LEBs.
- Embedded JIT as Slipstream's backend or threading solution: it runs Goose-generated C and still rejects workers; it does not replace the Wasm backend.
- Coroutine syntax in `b6688e17`: a design note (`docs/design/coroutines.md`), not implemented scheduler/async functionality in this delta.
- Contract/proof ideas in `51c4fe19`: proposed directions in `docs/design/llm_frontier.md`, not new usable `requires`/`ensures` features.
- Nested-growth notes `03b71f09`, `13cafbd3`: representation/iteration design discussion, not arrays of independently growable owning objects.
- C++/Rust translation guide `7ebac54b`: useful recipes for already-counted roots/pools, not an extra language feature; its upstream shared-memory comparison does not override this fork's native-memory contract.

## Delta classification and follow-through

The root/pool series includes considerable implementation tuning that must not be counted as separate adoption features: component caching (`ff9e9967`, `43e3fc9c`), known-owner propagation (`ead1c38b`, `231b22c5`), and non-escaping root parameters split into descriptor members (`5d1b5038`). The latter passes component addresses/headers/stack handles separately and reconstructs a local descriptor; escaping, captured, stored or fixed-entry references retain the conservative representation. Evidence: `docs/design/root_structs.md:248–263` and `:484–503`, `src/codegen_frames.h` (`FindSplitRootParams`). It improves the economics of item 1 automatically, but adds no user-visible storage permission and makes no Slipstream speed promise.

Likewise, bulk default/fill lowering (`ac908700`, `95a149e5`, `e2a878e5`), redundant-check removal (`ef2a88fc`), and pool search/tree optimizations (`79e0f7eb`, `a81a1296`, `32331557`, `f537e04c`, `93f1ad0a`) are implementation improvements behind existing/new APIs. The separate typed-extern relaxation inside `93f1ad0a` is counted in item 7. `53f08ad8`, `6638f268`, `8997e315` and the other measurement/migration commits supply benchmarks or examples, not additional language features. `33f952fb` demonstrates explicit flat worker snapshots; copying allocator internals is not a stable transfer API. Legacy pools are deprecated but still available (`777cab95`, `3dbf2639`).

Other correctness repairs stay outside the ranking: packed alignment/Clang ABI (`cec434a5`, `1213ac3b`), reassociation (`350af9d8`), float formatting (`24a2aad8`), EOF handling (`4df99ae1`), tail recursion (`61e30009`, `38614b75`, `0a10fa00`, `40369bd1`), dependency/provenance/cache tracking (`6fe4d11d`, `174e7988`, `a4af9402`, `bc915107`, `afa82534`), and LSP synchronization/insertion/cache fixes (`c47437bb`, `3320e1e9`, `18196a70`). ASCII vectorization (`fd6cc97e`), stdin lock amortization (`b9733b81`), runtime string splitting (`a532c801`), stdlib path normalization (`4bfa716e`), grammar rebuilds and fixture/format cleanups likewise add no adoption surface. The three explicit pattern/workflow-unlocking fixes retained above are justified individually.

The first follow-up should be a narrowly scoped root-owned writer/workspace experiment and a separate byte-copy cleanup, with matched correctness and performance checks. Pool adoption should wait for a specific independently reclaimed workload. Preserve streaming validation, compact IDs, native ABI layouts, collector budgets and worker isolation throughout. This survey authorizes none of those implementation changes.
