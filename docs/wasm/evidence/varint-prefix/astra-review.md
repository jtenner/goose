Independent review of Goose unsigned-LEB array-length prefixes

Review date: 2026-11-07. Repository: `/home/dev/Projects/goose-wasm-backend`. Branch: `feat/wasm-multimemory-backend`. Baseline and current HEAD: `d1044b66e3dd96b71a9bbfd530e0f00b220296fa`. Scope: the 21 uncommitted files in `/tmp/goose-wasm-varint-prefix-20261107/review-scope.json`.

**Result: no confirmed correctness defect found in the admitted scope.** The source supports canonical unsigned LEB128 array counts with fixed-size scalar and admitted ordinary-reference elements. I found no new route around the layout, adaptation, assignment, or by-value gates. This is a source and saved-evidence assessment. It is not a claim of minimum cost, improved speed, or complete test coverage.

I worked alone. I did not edit production files, build, compile, run tests, execute guest modules, debug, benchmark, acquire a lease, or contact another thread. I used file reads, hashes, byte comparisons, Git object reads, and a static parser of saved Wasm metadata. The only file written for this review is this report.

**Correctness and design assessment**

1. `src/wasm_memory.h:149-188`, `ReadPrefix`: the cached function index is assigned before body emission. All imports are established before functions in `WasmCodeGen::Run`. Body storage uses the function index, not a reference into a vector that could move. The helper signature is `(i64) -> (i64, i32)`. Its four locals are decoded bits (`i64`), width (`i32`), current byte (`i64`), and byte offset (`i64`). The saved module metadata agrees with these local types.

   Dispatch selects the high unsigned 32-bit memory identity once. Each case uses concrete memory operands for all loads. The one-byte path loads an unsigned byte, so its signed comparison with 128 is safe. The continuation path uses the masked low offset plus width in `i64`; it checks against `UINT32_MAX` before wrapping to `i32`. It cannot carry into another memory identity. Physical memory bounds remain enforced by Wasm loads. Invalid memory identities take error 7; address overflow takes error 11; invalid encodings take error 13.

   The continuation index starts at one. At index nine, only byte 1 can pass: zero is nonshortest, and any byte above 1 is rejected. Thus shifts stop at 63, the helper reads at most ten bytes, and it preserves all unsigned 64-bit bits in its `i64` result. A terminal zero after the first byte is rejected. Interior zero payload groups with continuation set remain valid. The loop's `br_if 1` exits its surrounding decode block; `br 0` repeats the loop. Each case then exits the Dispatch result block. The two result locals are loaded after that block. I found no branch-depth or multi-result stack error.

2. `src/wasm_codegen.h:48-64`, `src/wasm_arrays.h:59-75,217-389`: prefix sizing and writing agree. The count-based width calculation uses unsigned shifts. `InitArrayCount` uses the existing canonical ULEB encoder. That encoder accepts only `u32`, but every admitted constructor first proves that prefix plus payload fits Memory32. Every admitted element has positive fixed size, so the count passed to it fits `u32` and needs at most five bytes. Empty arrays still reserve and write their one-byte zero prefix. The old fixed-prefix range check is redundant but harmless for a correctly sized varint prefix.

   Full destination reservation occurs before element initializers. The fill value is evaluated once, including a zero-count fill. Literal elements retain source order. String bytes are copied with their exact length, including embedded NUL bytes. These paths use the existing cleanup records. Global owners retain their storage; local owners restore their saved tops. No native C lowering or shared layout definition changed. `ValueLayout::ArrayPrefix` still defines the fixed prefix offsets and the dynamic-offset sentinel; `LenStore` supplies the same varint storage discriminator used by native lowering.

3. `src/wasm_arrays.h:107-183`, exact-layout copy: admission uses the stored type of identifiers, indexed reference elements, direct call results, and inlined call results. It does not trust an adapted expression type. Unequal layouts fail before a copy is emitted. Source evaluation occurs once. The source base and decoded count are captured before destination reservation. The unsigned count/stride guard precedes multiplication; a second guard includes the decoded prefix width before narrowing to `i32`. `Reserve` also checks old top plus the full byte count and publishes the new top only after growth succeeds. Copying starts at the source header and includes the original prefix bytes. Packed offsets remain valid across memory growth; no host buffer view is held by this guest code.

4. `src/wasm_arrays.h:491-531,590-619,630-707` and `src/wasm_codegen.h:488-517`: indexing captures the length and width before index effects. Byte snapshots decode once and use the same width for the payload address. Equality captures each operand's width outside its element loop. Array iteration reloads a mutable reference or indexed path as required, then reads that iteration's current count and width. This permits rebinding from a one-byte prefix to a wider prefix. Nested path steps still use the existing fallback decode in `ElementOffset`; this is safe for immutable count prefixes, but can repeat work.

   Null checks remain in reference dereference and path loads. Byte printing handles a null optional before it attempts a prefix read. The host snapshot owns a copy before later argument effects. Reference-element copies preserve address bits; reference-element rebinding and pointee mutation remain distinct. Native equality of stored ordinary-reference elements also compares identity.

5. Mixed-prefix equality is not established by the same-prefix fixtures. I traced it separately through `src/typecheck_exprs.h:958-962,1900-1927`. For arrays of the same element type but different layouts, the checker creates `SliceExpr` operands with `WholeSlice`. Wasm has no slice-expression lowering, so this path is rejected. It does not reinterpret fixed-prefix bytes as varint bytes. For example, equality between `u8[varint]` and `u8[u16]` owners follows this slice gate. This conclusion is from source inspection, not a new execution.

   General `Convert` is not a layout-adaptation implementation. Its safety here depends on the caller gates and checker contracts. `FitsAt` requires equal pointee types for ordinary reference binding, while `InitArrayCopy` checks stored layouts for construction. Whole-array assignments fail in `Assign` and `AssignElement`. Direct by-value parameters/results fail in `Run`; inlined by-value bindings fail in `Statement`; array-valued temporaries have the existing `Gen` gate. Scalar varint elements, relative references, direct array elements, resizable-header reference elements, structs, slices, and other unsupported layouts still fail in `Type` or the expression/builtin gates. Serialization builtins remain unsupported. I found no new bypass in the callers inspected.

**Evidence and provenance**

- All 31 frozen changed/context file hashes match `review-source-hashes.json`, the current repository files, and the continuation manifest. All 4,144 entries in the continuation manifest match current file bytes. The build and continuation manifests differ only at `test/wasm_backend.py`.
- The six baseline copies match the exact pinned Git objects. `source.diff` exactly matches the scoped tracked diff from the pinned baseline. There are 13 tracked changes and eight new fixture/expected files.
- Both `goose-tested` and repository `build/goose` hash to `6f110d8e62ab7e5bae82eee65d42aa82bc979058ac2abb6203a1adea01360b66`. The prior compiler hashes to `8cf49b9eb51ef6c312cedb1222d32e17f18c6c33bcf659cc4586c3e016bc78b7`. The build record reports success. The saved/current build configuration is Release with `-O3 -DNDEBUG`. Hash agreement and the recorded build sequence support provenance; I did not independently rebuild the executable.
- `initial-harness.py` matches the build-input manifest. The frozen final harness matches `continuation/final-harness.py`. Their only difference selects native text `index 128 out of bounds (length 128)` for the new failure case. The initial failure log shows that both native and Wasm rejected the intended index. It was an expected-text mismatch, not evidence of a production failure. No production or host-adapter change appears between the two manifests.
- All 32 golden command records have the expected exits. All eight prior-target attempts reject with the old missing-prefix diagnostic. The four source fixtures match their golden source copies. Native outputs at Goose O0 and O2 match each other and the expected files. The golden C build commands use `cc -O0` at both Goose optimization levels. These raw golden runs do not establish C `-O2` execution. The full harness source does use matching C optimization flags for ordinary fixtures, but its successful subprocess output is not saved separately.
- All eight targeted module hashes and sizes match `targeted-results.json`. The saved emission, validation, native, Node, Wasmtime, and completed-owner runs have exit 0 and empty stderr. Node, Wasmtime, and owner stdout match the saved native stdout.
- The continuation records report 455 full-suite checks passed, 52 exact artifact/diagnostic comparisons, and 92 unchanged prior modules. I independently compared all 52 saved artifact pairs and their stdout/stderr/exit files. I also compared all 92 old/new Wasm pairs, their recorded hashes/sizes, and stdout/stderr/exit files. All match. The 52 comparisons use `goose-inline-checkpoint` as reference, whose recorded hash is `63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`; this is a different reference from the prior array-copy compiler.
- The saved `memory-runtime.wasm` and `memory-copy-matrix.wasm` match the corresponding final `build/gen/wasm` files. Both Node and Python test sources cover full 64-bit decoded values, malformed encodings, memory bounds, and invalid memory identities. The 65-memory tests exercise each concrete decoder case. Their execution evidence is the full harness summary, not separate per-subprocess raw logs.
- Completed-owner checks run synchronously through `_start` return, then inspect frame/data stack tops and memory objects. The prefix fixture checks persistent bytes `[128, 1]` plus 128 payload bytes and top 131. Scoped owners must return to top 1. These are owner-state assertions, not sleep-based completion assumptions.
- Initial and continuation lease/release records show their respective exit 1 and exit 0 and report child cleanup. I only read those records. `continuation/unit.exit` is absent. `continuation/unit.stdout`, `lease.json`, and `release-verification.json` record completion, and each substantive continuation command has its own exit file. This is a missing aggregate exit artifact, not a compiler defect.

**Performance and memory cost**

The added decoder has no guest heap allocation, scratch buffer, or memory growth. It uses four scalar locals and bounded work: one initial load, then at most nine continuation loads. Real constructed Memory32 arrays need at most five prefix bytes. There is one helper call and one memory Dispatch per decode, even when the caller knows the memory. Engine lowering of Dispatch and function calls is not measured.

Emission creates one cached decoder body per module, with a copy of its decode case per physical memory. Emission work and helper code size are linear in memory count, bounded by the backend's 65 total memories. The compiler uses its existing growing strings and vectors to hold this code. Those containers can allocate. Constant prefix writing also creates a small string of at most five bytes; a no-heap-allocation claim would depend on the library implementation and has not been measured. Dynamic prefix writes can add cached access helpers per byte offset. `WasmModule::Finish` retains its existing linear code assembly/copying costs.

The existing fully dynamic copy dispatcher has up to a quadratic number of memory-pair cases. This change does not enlarge that algorithm, but newly admitted varint copies can require it. Known source/destination memories still emit a direct `memory.copy`.

Indexing and snapshots reuse a decoded width within the operation. Equality decodes before the element loop and remains linear in compared elements. Iteration decodes at each loop test to preserve reference rebinding. Nested reference-array walks can decode a parent twice, once for bounds and once for its element offset. This is bounded by path depth and prefix width, but is an unmeasured cost. It is not evidence of a regression that requires a wider fix. Count sizing and writing are bounded by integer width. Explicit element literals still emit work per element; fills emit a loop with constant-sized construction code. Guest filling, copying, and byte snapshots remain proportional to payload size.

Static metadata read from the saved artifacts:

| Artifact | Total module bytes | Memories | Decoder body bytes | Maximum function locals |
| --- | ---: | ---: | ---: | ---: |
| values O0 / O2 | 10,932 / 10,932 | 11 | 1,785 | 168 / 168 |
| paths O0 / O2 | 8,112 / 8,159 | 7 | 1,149 | 145 / 168 |
| bytes O0 / O2 | 4,747 / 4,723 | 6 | 990 | 95 / 107 |
| cleanup O0 / O2 | 8,134 / 8,134 | 5 | 831 | 100 / 100 |
| memory-runtime | 3,830 | 3 | 513 | 4 |
| memory-copy-matrix | 122,759 | 65 | 10,371 | 4 |

Decoder body sizes include local declarations and the final end opcode. They exclude its name/type/function-section overhead. These are byte counts, not speed results. All 92 old-module pairs are byte-identical, which supports no emitted code-size change for that saved corpus. The old compiler rejected the new fixtures, so those fixtures have no old successful Wasm runtime baseline.

Guest reservation includes the complete prefix and payload. The allocator grows in 64 KiB pages. Cleanup restores tops; it does not shrink linear memories or prove that physical pages were returned to the OS. Printing still allocates host-owned byte snapshots and output buffers proportional to printed bytes. The extension adds a prefix decode to that path, not a second payload snapshot.

There are no controlled compiler CPU, RSS, allocation, guest timing, or physical-memory measurements. Runtime speed, compiler-time cost, allocation totals, and minimum memory footprint are therefore unproven. Linux x86-64, Node 24.22.2, Wasmtime Python 49.0.0, and wasm-tools 1.262.0 provide functional evidence only. Guest page counts do not measure OS residency. There is no native runtime evidence for other architectures.

**Coverage gaps and unverified risks, separate from defects**

- `test/wasm_memory.mjs:18-40` and `test/wasm_memory.py:36-56`: the `0xffffffff` address is outside the small test memory on the initial load. It does not reach error 11 after a successful load at the final Memory32 byte. The no-carry argument is supported by source inspection, not that execution check. A future controlled boundary test should specifically assert error 11 after a continuation byte at the last address. No such test was run here.
- The helper tests omit explicit shortest-encoding controls at several intermediate widths and do not test every full-64-bit boundary. The source logic is sound on inspection. Useful cases include an interior zero payload group, a terminal zero at a later width, and a ten-byte terminal zero.
- The new fixture set has no explicit mixed-prefix equality rejection test, varint-specific unsupported-element matrix, or varint-specific by-value/inlined argument/result rejection matrix. Existing copy-admission tests cover fixed-to-varint and varint-to-fixed prefix adaptation. The old generic gates remain present, but this does not substitute for those omitted regression cases.
- The saved varint fixtures do not directly exercise a corrupted decoded count against both new copy byte-total guards. Full-64-bit helper success is not coverage of full-64-bit array construction. Supported constructors cannot create those oversized arrays. A focused derived-module check could test rejection before reservation without allocating a huge payload.
- Varint-specific zero-fill side effects, optional-null byte printing, and an effectful index that rebinds a parent across prefix widths are not all isolated by the new fixtures. Existing shared paths and older tests provide related evidence. The source review found no defect, but related coverage must not be counted as direct coverage of each new combination.
- No controlled performance comparison is available. The known static costs above are acceptable design tradeoffs on inspection, but there is no measured basis to claim that they are minimal. No performance change was made in this review.

**Inspection record**

Every changed file was read in full from the frozen packet:

- `scripts/run_wasm.mjs`
- `src/wasm_arrays.h`
- `src/wasm_codegen.h`
- `src/wasm_memory.h`
- `test/expected/wasm_varint_bytes.out`
- `test/expected/wasm_varint_cleanup.out`
- `test/expected/wasm_varint_paths.out`
- `test/expected/wasm_varint_prefix.out`
- `test/wasm/wasm_varint_bytes.goose`
- `test/wasm/wasm_varint_cleanup.goose`
- `test/wasm/wasm_varint_paths.goose`
- `test/wasm/wasm_varint_prefix.goose`
- `test/wasm_array_copy_admission.py`
- `test/wasm_backend.py`
- `test/wasm_copy_matrix.mjs`
- `test/wasm_copy_matrix.py`
- `test/wasm_memory.cpp`
- `test/wasm_memory.mjs`
- `test/wasm_memory.py`
- `test/wasm_multimemory.mjs`
- `test/wasmtime_host.py`

Full context reads: `src/value_layout.h`, `src/wasm_binary.h`, `src/wasm_storage.h`, `src/data_stacks.h`, and `test/backend_shared.py`.

Relevant context excerpts read: `src/ast.h:65-135`; native count writing, copy/construction, and fill paths in `src/codegen_construct.h:1-110,350-460,760-880,1210-1320`; views, index evaluation, and equality in `src/codegen_values.h:340-480,640-695,1755-1808`; native ULEB runtime in `src/runtime/runtime.h:1100-1208` and its generated copy in `src/runtime_inline.h:1206-1318`. Additional repository context reads covered `src/typecheck_exprs.h:950-972,1080-1140,1280-1425,1800-1980`, `src/typecheck_flow.h:3180-3220`, `src/codegen_nodes.h:160-265`, and `src/codegen_types.h:1090-1125,1230-1310`. Searches in other checker files located related declarations; those searches were not full-file reviews.

Evidence inspected includes the scope, complete diff, both source manifests, source hashes, compiler hashes, golden identities/results and raw targeted/golden logs, build logs, initial/final harness difference, continuation scripts and records, both lease/release records, all compatibility/equivalence artifact pairs and logs, and the saved modules' static metadata. The six baseline files were checked against Git and reviewed through the scoped diff; I did not separately reread every unchanged baseline line.

No changed file is unread or missing. Large context files were read only in the relevant portions listed above. Generated native C files and all unchanged test fixtures were not reviewed in full. Successful full-suite subprocess logs are not separately available; its aggregate summary and checked harness are the evidence limit. `continuation/unit.exit` is missing as described above. The stage uses `golden-identities.json` and `golden-results.json`, rather than a `golden-identities/results.json` directory layout. No missing file prevented this read-only review.
