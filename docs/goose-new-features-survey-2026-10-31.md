# Newly arrived Goose language features for Slipstream

Survey requested 2026-10-31; researched 2026-11-01. The best immediate candidates are **root structs for state ownership** and **`move_from` for existing copy loops**. The ranking covers syntax, type-system rules, semantics and memory constructs only; standard-library APIs, packaging, tooling, editor support and pure code generation changes are confined to the unranked appendix.

## Scope and evidence

This surveys the 118 upstream commits in `64d62fc7..40369bd1`, using the requested rebased fork snapshot **`4abab61546ca4e7266005fc3a1cadb35618ab99c`** for all Goose file/line references. The commit list, functional documentation changes, relevant implementation diffs, and regression fixtures were inspected. There is **no CHANGELOG file in that tree or changed in this delta**; the commit history and changes to `docs/reference.md`, `docs/stdlib.md`, `docs/packages.md`, `docs/goose_spec.md`, `docs/implementation.md`, and design/testing documentation supply the change record.

Slipstream is available at `/home/dev/Projects/slipstream`, HEAD **`781e53d2e10ebe8d9ac415c350f25081c6127b1b`**. Its source was inspected read-only. Existing changes to `experiment.md` and untracked `experiment-results.md` were left alone and were not evidence for these conclusions. Slipstream references below are relative to that repository; Goose references are relative to this repository. Line numbers refer to these snapshots, not future master.

A source search over Slipstream's Goose and build files found no `root struct` declarations, calls to `move_from`, `range_index` or `check_length`, or extern growable-array parameters. Consequently, global-root field index/link types are not adopted either. This establishes absence of direct adoption in the inspected source, not absence of transitive compiler/runtime benefits. The fork already contains the upstream implementations, samples and tests; those are not independent adoption by Slipstream. The version of existing executables cannot be inferred from source.

Ratings concern implementation payoff: **PROVEN** means a concrete existing source pattern that the capability directly simplifies; it does not mean a migration or speedup was tested. **PLAUSIBLE** means a clear fit with unmeasured pain or integration cost. **SPECULATIVE** means a conditional future use. No compilation, benchmarks, code changes, publication or build artifacts were needed; the only deliverable change is this survey.

Language builtins such as `move_from`, `range_index` and `check_length` belong in the ranking: the compiler defines and type-checks them (`src/builtins.h`, `src/typecheck_builtins.h`), and no standard-library import is required. Conversely, `alloc_with` is a library API built on existing destination construction and generic callbacks, not new generic syntax. The delta adds generic root structs, but no separate new generic-constraint or specialization syntax was established. The fork's `build::` constants, `const if`, shared-memory capabilities and `UnsafePtr` are not newly introduced upstream language features in this range. Proposals are not counted as shipped constructs.

## Ranked language features

### 1. Root structs own several independent arrays — PROVEN

**New capability.** One local/global owner can hold several independently growing fields, with one lifetime and references passed to helpers. This removes the ordinary struct's single-resizable-tail restriction. Commits `a01815f7`, `9e427c33`, `683ebc94`, `d096b132`, `6b4d3c34`, `e2923724`, `7c41c58a`, with published contract `cbc64a32`. Evidence: Goose `docs/reference.md:1344` (Root structs), `docs/goose_spec.md` §3.4; the component allocation is implemented in `src/codegen_stmts.h` (`BindLocal`).

**Current use and target.** Not adopted. Slipstream `gc/heap.goose:14–55` separately declares more than twenty backing arrays and wires them into `Collector`; `src/model.goose:50` does the same through `Module` references; `src/stack.goose:33` through `Machine`; `src/amd64.goose:13` through `Writer`; `src/redline_ir.goose:40–69` through analysis/SSA/function contexts. A local root owner can absorb backing-array declarations and much of this constructor wiring while helpers continue to borrow it. The clearest first target is a small compiler writer or optimizer workspace, followed by collector state once its budget calculations are preserved.

**Reference and generic semantics.** Root structs can be generic; each field has independent storage identity, so shrinking scratch need not invalidate a view into items. A root reference can itself be stored in an ordinary context, made optional, returned or captured while its owner lives (`docs/reference.md:1357–1393`). This lets Slipstream separate a workspace owner from borrowed writer/analysis interfaces, rather than carrying every backing-array reference separately. These are parts of the root feature, not new general-purpose generics or relaxed arbitrary aliasing.

**Limits.** No nested owners, owner arrays, by-value returns, whole-owner serialization, public C layout, or worker transfer. Keep ordinary packed ABI records and independently scoped child owners. Existing callback scopes may still be needed to bound lifetimes. Roots do not loosen the fork's shared-memory rules.

### 2. Checked overlap-safe slice copying — PROVEN

**New capability.** `dst.move_from(src)` checks equal lengths and copies fixed-size, copyable elements with memmove semantics; it does not clear the source. Commit `d24161f4`; Goose `docs/reference.md:907–936`, `src/codegen_builtins.h:251` (emits `memmove`).

**Current use and target.** Not adopted. Slipstream `gc/heap.goose:555` copies collector bytes in a loop; `src/redline.goose:23–30` copies chunks into the output buffer element by element. Equal-length byte slices express both directly. This removes hand-written indexing, with overlap safety useful for future optimizer buffer edits. The collector currently documents nonoverlapping relocation, so do not claim it has an overlap bug.

**Limits.** Preserve admission/bounds checks and chunk flushing. Self-relative elements cannot be copied this way, and raw native addresses/shared capabilities are not ordinary slices. Actual throughput versus the existing optimized loops is unmeasured.

### 3. Native functions can fill typed growable arrays — PLAUSIBLE

**New capability.** `extern fn` accepts `T[>..]&` for any flat fixed-size `T`, extending the former byte-builder-only allowance. Hidden inside the pool-runtime commit `93f1ad0a`: `src/typecheck_calls.h` changes `ExternParamOk` from `IsU8` to `ExternValueOk`; Goose `src/runtime/goose.h:1–10` documents the contract; `docs/reference.md` §23 and `docs/packages.md:237` describe it.

**Current use and target.** No extern growable-array parameter found in Slipstream. A future native helper producing `Relocation { at, label }` records could fill the compiler writer's relocation array directly (Slipstream `src/amd64.goose:9–14`), removing an intermediate native buffer and a Goose copy loop if such a helper is introduced. The current writer already emits in Goose, so this is not a demonstrated current bottleneck. `slice_pool_internal.goose:12` is an actual upstream user of a struct-element builder.

**Limits.** C must respect packed element size, initialization, stack top/header count, capacity and borrow lifetime. `gs_bld_append` remains a byte helper, not a new generic append routine. This does not permit native code to retain the borrowed builder or share it across threads. Avoid introducing native helpers where ordinary Goose already suffices.

### 4. Reset borrowed fields before reusing their buffer — PLAUSIBLE

**Unlocked pattern, retained under the brief's fix exception.** Assigning static data such as `""`, rebinding an optional reference to null, or resetting a holder to a literal with such defaults now proves that the holder no longer borrows shrinkable storage. A helper can clear those fields, shrink/refill its buffer, and repopulate the views on repeated calls. Commit `0357b1c2`; Goose `docs/implementation.md:2298`, `test/lifetimes/emptied_static_fields.goose:14–30`, with negative path/other-field fixtures.

**Current use and target.** No demonstrated occurrence of that exact repeated reset/shrink pattern in Slipstream was established. A concrete application would be a reusable optimizer scratch owner plus a view record: clear all borrowed view fields before resetting the backing arrays, then refill and rebind for the next function. Slipstream already has borrowed optimizer state records in `src/redline_ir.goose:40–69`; this would simplify adding such a repeated scratch-buffer API without per-iteration wrapper scopes. No present compiler rejection of that code was established. Existing streaming reader policy explicitly avoids retaining metadata pointers into input (`src/reader.goose:7–8`); preserve that policy.

**Limits.** Every relevant path/field must release the borrow. Assigning another dynamic slice is not a release, and this is a lifetime-analysis improvement, not shared-memory release or deallocation.

### 5. Recover a slice's checked position in an array — PLAUSIBLE

**New capability.** `array.range_index(slice, message?)` accepts slices whose exact origin is not known statically and returns their starting element index after checking nonempty containment and alignment. This extends what can be expressed beyond `index_of`, which requires a reference statically rooted in that array. Commit `d6a3ceaa`; optional literal failure messages added by `52282722`. Evidence: Goose `docs/reference.md:913–928`, `src/codegen_builtins.h:467`, `src/typecheck_builtins.h` (`B_RANGE_INDEX`).

**Current use and target.** No calls found. For a future slice-returning collector arena or optimizer range-edit helper, recover the offset from the owner's array at the boundary instead of passing a parallel offset or implementing pointer arithmetic. Slipstream's `Types { pos, len }` representation (`src/model.goose:5`) and optimizer ranges (`src/redline_ir.goose:64–69`) provide a concrete target: convert an ordinary returned slice into a checked start/length record. This is useful only if a new helper naturally works in slices; existing index-based code needs no conversion.

**Limits.** Empty slices from any origin return zero, so they lose any original empty-range position. Containment does not prove allocation liveness or prevent double frees. The result is i64, not an automatically narrowed u32 index; preserve width and application-budget checks. It does not convert shared capabilities or raw native addresses into safe slices.

### 6. Validate an array element count before mutation — PLAUSIBLE

**New capability.** `array.check_length(n, message?)` rejects negative or oversized counts, including oversized unsigned counts, against the data-stack reservation for the fixed-size element type, and returns the checked count without allocating or changing the array. Commit `d6a3ceaa`; custom literal messages `52282722`. Evidence: Goose `docs/reference.md:914–929`, `src/codegen_builtins.h:462` and its `SliceLen` lowering.

**Current use and target.** No calls found. Slipstream collector setup calculates backing-byte and metadata counts before populating arrays (`gc/heap.goose:15–47`). A checked count at an internal array-growth boundary would centralize the language's element-size/reservation guard for backing bytes, handles or scratch entries, rather than duplicating that particular machine limit in each helper. This complements, rather than replaces, the existing collector budget calculation. The same pattern fits internally admitted optimizer scratch counts.

**Limits.** This aborting guard is not suitable as a replacement for recoverable validation of malformed Wasm or the collector's `false` admission result. Preserve those checks first. It neither reserves storage nor checks remaining space after existing contents, and it does not validate arithmetic that already overflowed while calculating the count. No currently missing guard or performance benefit is claimed.

### 7. Compact links and index types can name global-root fields — SPECULATIVE

**New capability.** `Node&<u32 in graph.nodes>`, `u32 in graph.nodes`, and `u32 upto graph.nodes` can name a mutable, direct grow-only array field of a global root owner. The field's storage identity is part of the type; another field or owner is a different array. Commit `56bbde07`; Goose `docs/reference.md:1395–1400`, `docs/goose_spec.md` §3.9/§3.11, `src/typecheck_types.h` (`NamedArrayComponent`, `ValidateNamedComponents`), and `test/typing/root_component_index.goose:1`.

**Current use and target.** Not adopted. A future single-owner, single-thread optimizer graph could retain compact links while grouping node/edge arrays under a root, and typed node IDs could reject mixing graph arrays. Slipstream currently stores raw u32 node/edge identifiers (`src/redline_ir.goose:64–69`), so that is the implementation work the construct could ease. No need for a global graph was demonstrated.

**Limits.** The type name cannot target a local owner, traverse aliases/references, or select nested fields. Slipstream's per-instance and parallel contexts are a poor fit: do not globalize them merely to gain typed indices. This limitation makes the item speculative despite the implemented language support.

## Language boundaries and negative space

- Whole-root worker transfer is unsupported; construct worker-local roots and retain the fork's shared-capability rules (`docs/reference.md:1407–1415`).
- Nested root owners, arrays of owners and by-value root factory results remain unavailable; they cannot express a runtime array of independently growing Wasm instances (`docs/reference.md:1402–1415`).
- Root layout is not a native ABI or serialized image; preserve packed collector/host records and serialize eligible components separately (`docs/reference.md:1407`).
- Global-root named indices fit a single global owner, not Slipstream's existing per-instance/parallel graph contexts (`56bbde07`, `docs/reference.md:1395`).
- Coroutine syntax (`b6688e17`) remains a proposal, not a shipped scheduler construct (`docs/index.md:99`, `docs/design/coroutines.md`).
- `requires`/`ensures`, `abortfree`, `pure` and proof-based parallelism in `51c4fe19` are research proposals, not usable new contracts (`docs/index.md:102`, `docs/design/llm_frontier.md`).
- Nested-growth/append-handle discussions (`03b71f09`, `13cafbd3`) do not implement nested independently growable containers (`docs/design/nested_growth.md`).

The ranking retains `0357b1c2` under the brief's exception for fixes that unlock previously rejected patterns: the change is in lifetime acceptance, not merely emitted code. Existing-language correctness repairs to packed ABI, reassociation, tail recursion and generic named-array dependency tracking are not new syntax or type-system facilities. In particular, `afa82534` repairs generic cast dependency accounting rather than adding a generic feature.

The first implementation follow-ups would be a root-owned writer/workspace experiment and a separate byte-copy cleanup, each with matched correctness and performance checks. Preserve streaming validation, compact IDs, native ABI layouts, collector budgets and worker isolation. This research-only survey implements none of those changes.

## Appendix: other changes, unranked

- Binary readers (`23a7533b`; `docs/stdlib.md:1029`): no Slipstream import found; could simplify fixed-width optimizer decoding, but are library functions, not new bit-cast syntax, streaming reads or LEB decoding.
- `slice_pool` (`fa1b1640`, `17c512ef`, `2bbc8f34`; `stdlib/slice_pool.goose:9–94`): unused in Slipstream; reusable optimizer ranges are a possible fit, but retained high-water storage and stale views do not replace collector reclamation.
- `slot_pool` and builders (`71ca3687`, `0e34d3a7`, `0356ddae`; `stdlib/slot_pool.goose:6–69`): unused in Slipstream; possible mutable-graph storage, with no tracing, generation or occupancy checks.
- Legacy-pool deprecation and worker snapshot examples (`777cab95`, `3dbf2639`, `33f952fb`; `docs/stdlib.md:566–606`): migration guidance only; explicit flat snapshots do not add root transfer semantics.
- Package `c_headers` (`6ac5828c`, documentation `2ed1a63d`; `docs/packages.md:175–196`, `:258`): no Slipstream use found; packages can own inline native adapters, without a new Goose type or C-import syntax.
- Root component caching and split parameters (`ff9e9967`, `43e3fc9c`, `ead1c38b`, `231b22c5`, `5d1b5038`; `docs/design/root_structs.md:248–263`, `:484`): automatic lowering optimizations behind roots, not new permissions or ownership constructs.
- Pool tree and bulk initialization tuning (`93f1ad0a`, `ac908700`, `95a149e5`, `e2a878e5`, `ef2a88fc`; `stdlib/slice_pool_internal.goose:12`, `docs/implementation.md`): implementation improvements, with the separate extern type relaxation ranked above.
- Relative-field destination construction (`78744fda`; `src/codegen_construct.h:1002–1013`): repairs emitted code for already-accepted pushed literals; no matching Slipstream use established, and no new language feature ranked.
- Deterministic generated C (`2c7d8d5a`; `src/codegen.h:1548`, `test/emit_order.py:1`): automatic benefit for fork reproducibility investigations, not a language construct or identical-binary guarantee.
- Caller-site library diagnostics (`52282722`, `2b509397`; `src/codegen.h:224–249`, `src/typecheck.h:592–603`): automatic debugging aid for Slipstream's existing std/os calls; the distinct builtin message arguments are covered in the ranking.
- Hosted JIT and conditional SELinux mappings (`cce94b91`, `00329a57`; `docs/design/jit_backend.md:33–83`, `cmake/libtcc.cmake:60–63`): possible fork reproduction/packaging benefit, not Slipstream's Wasm backend or new thread support.
- Generic UFCS completion and LSP repairs (`5b0fdc61`, `c47437bb`, `3320e1e9`, `18196a70`; `src/lsp_features.h:1871–1894`): editor assistance only; personal usage unknown and generic call semantics unchanged.
- Documentation search (`3cc84860`; `docs/site/generate_search.py:44–90`): developer research aid, not a runtime index or language feature; personal usage unknown.
- Declaration alignment (`8f528987`; `src/format.h:545–570`): formatter behavior only; no Slipstream Makefile invocation found.
- C++/Rust recipes, benchmark refreshes and migrations (`7ebac54b`, `53f08ad8`, `6638f268`, `8997e315`; `docs/Goose for C++ and Rust Programmers Translating Common Patterns.md`, `bench/slot_pool.md:14`, `bench/slice_pool.md:14`): guidance/evidence for existing facilities, not extra language features or measured Slipstream gains.
- Other library/runtime cleanups (`24a2aad8`, `4df99ae1`, `fd6cc97e`, `b9733b81`, `a532c801`, `4bfa716e`): float formatting, EOF handling, ASCII vectorization, stdin locking, runtime strings and path normalization add no language adoption surface.
