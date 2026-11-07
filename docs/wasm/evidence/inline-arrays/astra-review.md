Independent review of the frozen candidate, 2026-11-07

No confirmed defect was found within the admitted subset. This is a source and saved-evidence review. It is not a new execution result or a performance approval. No compiler, build, test, validator, timing job, or guest module was run. No source was changed. No other agent or reviewer was used.

The baseline is `69ca4f1f661159929f228799556bc4ddb8a5f2a9`. The reviewed files are under this packet's `candidate/`. No later worktree source was used. There is no PR. Prior review conclusions were not used as evidence.

**Confirmed findings**

None. I found no valid-input case that establishes a new correctness failure in this frozen candidate. The open items below are coverage and measurement limits, not confirmed defects. They do not have a defect severity or a proposed code fix.

**Identity and evidence checks**

- All 39 changed files match the SHA256 values in `scope.json`, including the new files that are absent from `tracked.diff`.
- All eight tracked diff entries have baseline blob IDs that match the stated commit and candidate blob IDs that match the frozen files.
- All 83 supplied source files named in the final source manifest match their hashes. All four harness hashes match. Five named build inputs are absent: `CMakeLists.txt`, `cmake/libtcc.cmake`, `cmake/linkclosure.cmake`, `cmake/package.cmake`, and `cmake/version.cmake`.
- The frozen native equality, indexing, iteration, frontend equality, shared layout, Wasm memory, and Wasm storage files inspected against the baseline are unchanged at that commit.
- All six preserved executable sizes and hashes match `compiler-identities.json`. The final executable is 6,987,808 bytes, SHA256 `63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`.
- The source manifest embedded in `equality-validation.json` equals the final standalone manifest. Earlier embedded manifests describe earlier builds and must not be treated as the final build.
- All 56 supplied before/after module pairs are byte-identical. Their sizes and hashes also match `prior-wasm-summary.json`. Their baseline is the query-repair compiler `d3969a0a8241d8a316fed09577c93bf75db1a9280f723356712574e3dfc4fc25`, not the original data-stack commit.
- All nine new fixture source hashes match `module-sizes.json`. Sixteen of its 18 module size/hash entries match supplied final modules. The two final fixture-path equality modules are absent. The supplied equality modules were emitted from the repair-path source and have different sizes. Their bytes were hashed separately; they are not substitutes for the two missing final hashes.

These checks establish file identity and consistency with the saved records. They do not independently prove that a compiler binary was built from the manifest. That link rests on the saved build, manifest, and validation records. A reproducible rebuild was prohibited and the packet does not contain all build inputs.

**Saved failing-first and after results**

I checked command records against the individual saved exit fields, and compared the saved native output with each engine and owner-check output. I did not rely only on summary booleans.

| Case | Before evidence | After evidence |
| --- | --- | --- |
| Indexed sequence paths | Four cases at O0/O2 give eight output mismatches. Native, Node, Wasmtime and validation commands exit successfully. The fixed path prints `1, 2, 3` in Wasm but `1, 20, 30` natively. The limited path stops after `1`. Effectful and nested paths also differ. | All 12 case/optimization combinations in the path archive match native output under Node, Wasmtime and the owner harness. Boundary and optional-reference cases already passed before repair and are not failing-first proof. |
| Array equality | O0/O2 modules validate but disagree with native output. Equal distinct arrays compare unequal in the old code. | Both saved equality modules match native output under both engines and the owner harness. |
| Unary array temporary | Native emits and prints `true`. Both old Wasm modules fail validation: expected f64, found i32. | Both compilations reject the unsupported temporary with a destination diagnostic. The saved check requires that no module exists. |
| Effectful equality | Native prints `true` then `9`. The old backend already rejects this case with a destination diagnostic. | The new backend rejects it with the specific effectful-comparison destination diagnostic. This is diagnostic coverage, not a newly repaired wrong-result case. |
| Nested type validation | The saved depth-40 compile reaches the five-second limit. The record identifies compiler `6c3b0cc8...`, source SHA256 `3194819c254fe0891318540e5a8e86dcd2dc33b9877b7aaee67cab7c0302944d`, empty captured stderr/stdout, and killed-child exit `-9`. The supplied source matches that hash. | The permanent harness generates the same source, compiles it natively and to Wasm at O0/O2, and checks `true` under both engines. Saved intermediate and final harness runs pass. |

The path command archives have 96 commands each; equality before/after have 34 and 32 commands. All command exit values agree with their separate exit records. Archived path sources match the permanent fixtures byte for byte. The equality source also matches its permanent fixture.

The final archive records 247 Wasm checks, a passing native baseline suite, 52 exact compatibility comparisons, and 56 unchanged prior modules. The final compatibility summary names the final compiler and the preserved data-stack compiler `8ee9634c...`. I verified its 52 entries and compiler identities, but the packet does not supply the paired raw C/diagnostic outputs needed to independently repeat those 52 byte comparisons. The native suite retains its stated device, platform and JIT skips. A suite exit of zero is not coverage of skipped cases.

The validation scripts use a nonblocking shared lock, wait for their children, reap descendants, and release the lock. Saved release records report owner exit, completed child collection, and a successful immediately released lock probe. These are saved observations. I did not acquire a lease or run a resource job.

**Code assessment**

- Packed layout and overflow: `wasm_codegen.h:79-99` validates the element once, then uses `FixedSize(element)` for the numeric guard. Admitted scalar/reference elements have positive stored sizes. Inline multiplication is bounded before the full size is used. Fixed arrays have no prefix; limited arrays use `LenStore` without padding. `wasm_arrays.h:18-29` uses unsigned 1/2/4/8-byte count loads and matching stores. Eight-byte inline counts cannot fit the admitted Memory32 allocation and have no claimed runtime coverage. The 255/256 and 65535/65536 fixtures exercise prefix transitions, last elements and pop.
- Address arithmetic: `ElementOffset` uses i64 arithmetic and checks the Memory32 result. Checked indices are unsigned-bounded by the live or captured length; negative indices therefore fail. The unbounded form depends on frontend/BCE proof, as before. Frame and static end checks bound the live allocation. Empty owners receive separate one-byte reservations for identity, without changing their logical value size.
- Widths and nulls: `FrameRef` keeps references to inline array storage as i32 even in a program with data memories. Stored ordinary references remain eight bytes. `LoadFixed`, `Load`, `StoreFixed` and `Store` perform the required narrowing or widening. `LoadElement`/`StoreElement` separate packed addresses from fixed-memory accesses. Indexed reference assignment changes its address-local width when it follows an i32 pointee. Bare null conversion and null checks use the target reference width. Growable owner references retain the existing 16-byte representation; unsupported compound elements remain rejected.
- Mutation: limited push evaluates the value first, then reads the current count, checks capacity, stores the element and publishes the count. This preserves changes made by the argument. Limited pop and clear change the count without changing a data-stack top. Fixed/limited bases stay stable. The frontend's limited-only cap rule prevents the newly routed builtin from treating growable arrays as static-capacity arrays.
- Iteration: `CaptureArrayWalk` and `LoadArrayWalk` agree with native `IndexLoc`, `GenLoc` and `ForLoop::CgStmt` for the admitted paths. Index values are captured once. An effectful index captures its parent view before the effect. Remaining reference slots reload each pass. Mutable reference roots reload; call roots execute once. Length is read at each loop test. Reference elements bind as their held reference; other by-reference elements bind to their address. Nested, effectful, mutable-root and limited cases have saved native-valid evidence.
- Equality: `wasm_arrays.h:234-261` compares lengths, then loaded elements, with early exit. Integer/bool operations compare scalar values. Float eq preserves equal signed zero and unequal NaN, including self-comparison of a NaN array. Ordinary reference elements compare identity, as native `EqX` does. The optional-reference branch in `BinaryValue` preserves the frontend/native identity contract for unnarrowed optionals. Cross-kind array equality is adapted to slices by the frontend and remains outside the admitted subset. Effectful RHS operands and array temporaries that need destination protection are rejected.
- Ordered cleanup: inline owners add no data-stack cleanup action. They reside in the function frame until normal function cleanup. Existing growable-owner restore actions and deferred bodies remain in reverse registration order. The existing ordered-cleanup fixture covers return, break, continue, nested defers and deferred allocations; its prior module pair is unchanged. This is useful shared-path evidence, but it does not cover every new inline-owner/defer combination.
- Sparse storage: `wasm_binary.h:88-119` keeps the logical end separate from serialized fragments. A reservation changes the address range without allocating a zero buffer for that range. Following data uses the logical end and preserves gaps. Finish sizes Memory 0 and its top from that end. The encoder test checks two gaps, interleaved bytes, alignment, engine-visible zeros and overflow rejection. The non-sparse path retains its former encoding.
- Diagnostics: unsupported constructors, by-value arrays, copies/temporaries, variable arrays and compound layouts stay outside the implementation. The harness checks valid native oracles for the new destination cases, specific failure reasons for capacity/bounds/pop, empty stdout on runtime failure, and absence of partial modules on the tested compiler failures.

**Unverified risks and coverage limits**

No item in this list establishes a defect. Each needs a targeted check before a code change.

| Area and source | Unverified case or cost | Narrow follow-up |
| --- | --- | --- |
| Equality, `wasm_arrays.h:248-254` | The equality fixture includes growable arrays, so scalar reference elements use packed i64 values. It does not directly exercise scalar-reference element equality in an inline-only program with i32 values. Optional reference elements and inline-array-reference elements also lack direct equality cases. | Add small native/Wasm comparisons for these element types, with equal aliases, distinct equal pointees and null elements, at both pointer modes. Require each case to check identity rather than pointee equality. |
| Equality, `wasm_arrays.h:253-254` | f64 NaN and f32 signed zero are covered. A separate f32 NaN and a same-array NaN comparison are not shown in the fixture. Source inspection supports the IEEE result, but no saved execution proves these combinations. | Add f32 NaN and self-comparison checks, including `!=`, if this matrix is expanded. |
| Cleanup, `wasm_codegen.h:275-299` and `wasm_arrays.h:59-96` | Existing cleanup and new inline fixtures cover shared behavior separately. The packet has no dedicated mixed inline/growable defer fixture that rebinds an inline-array reference during an early exit. | Add one native-valid mixed case with a specific output order and completed owner-state assertion. Do not infer correctness from inventory counts. |
| Compiler scaling, `wasm_codegen.h:64-99` and `wasm_arrays.h:272-315` | The duplicate recursive validation was removed. Type validation still repeats through helper calls. Across a nested path, recursive type work can sum to quadratic work in path/type depth. There is no CPU, allocation or stack-depth measurement. | Measure a controlled depth series against the exact baseline/candidate before claiming scaling gains or adding caching. Keep type validation separate from numeric size queries. |
| Large static ranges, `wasm_binary.h:88-119` | Source bounds checks cover near-Memory32 sizes, but saved runtime tests do not instantiate an inline owner near the address limit. Engine maximum-memory behavior is not measured. | Use an encoder-only boundary check first. Run a large instance only under an explicitly authorized resource limit. |

**Performance, code size and memory**

There are no precision runtime samples, compiler CPU measurements, compiler RSS samples, allocation counts, or physical-memory measurements for this stage. The five-second compile limit is a functional test. Native suite elapsed-time text is not a controlled benchmark. No native ARM, Windows or macOS runtime result is supplied. No speed ratio or physical-memory saving is established.

Source inspection gives these costs:

- Equality has O(n) worst-case element work and constant guest local storage. The previous address comparison was incorrect, so its O(1) cost is not a correct alternative. Each element currently incurs address calculation/checks and loads; dynamic growable references use existing dispatch helpers. No guest heap allocation is added by the equality loop. Relative runtime cost against native equality is unknown.
- Indexed iteration adds the reference loads and checks required by the live path. For path depth d and n visits, path work can be O(n*d). The compiler's walk vector uses O(d) storage and may allocate as it grows. Generated captured values are Wasm locals, not a runtime heap object. Repeated type queries can add compiler work as noted above.
- Fixed literal initialization emits work proportional to the number of explicit elements. Limited push/pop/clear have constant work per scalar/reference operation, apart from argument work and frame growth. Inline capacity increases addressable frame/static storage. Frame slots are not reused across disjoint scopes. Memory growth can retain backing storage after the top is restored.
- Sparse reservations avoid a capacity-sized compiler zero string and its serialized bytes. Compiler storage remains proportional to real data bytes and fragment metadata. Fragment vectors and strings still allocate, and Finish still copies serialized sections. This is a source-level allocation bound, not a measured total-memory result.

The supplied final inline-array modules are 8,815 bytes at O0 and 8,841 at O2 despite a global capacity of 65,536 bytes. These sizes and hashes are verified from the bytes. The encoder's exact 529-byte claim is not independently verified because its emitted module is absent; its source test enforces a size below 4,096 bytes while checking the reserved gaps.

Saved repair-path equality modules grow from 5,304 to 11,468 bytes at O0 and from 5,462 to 12,011 bytes at O2. These are verified file sizes: increases of 6,164 and 6,549 bytes for corrected semantics. They include diagnostic text and are not instruction-section measurements. The final fixture-path sizes of 11,688 and 12,247 bytes are record-only observations in this packet. All 56 prior module pairs match exactly. The final compiler executable is 17,480 file bytes larger than the preserved data-stack executable; this is not a text-section or compiler-memory measurement.

The resource harness waits for synchronous `_start` return, then checks the instance's actual stack tops and pending prints. It checks separate memory buffers and selected addressable sizes. It does not infer completion from a sleep, and it does not measure physical commitment or prove that memory.grow storage was returned to the operating system.

**Missing evidence and review boundary**

The packet lacks the five build files listed above, the two final fixture-path equality modules, the emitted sparse encoder module, and paired raw artifacts for the 52 compatibility checks. Several full-suite fixture files and helper files referenced by the harness are also not packaged, including `test/backend_shared.py`, `test/wasm_conversion.mjs`, and the four `test/typing` fixture sources and their expected files. The full native suite cannot be independently reconstructed from this packet. The saved depth-40 before source is present; the earlier depth-28 failure is described in prose but is not separately proved by the supplied raw records inspected here.

No fresh validity check, execution, validator run, build, timing sample or platform run was performed. Proposed coverage additions above have not been compiled and are not claimed as confirmed triggering sources. Related large frontend/native files were read only at relevant sections. Unrelated source and documentation were not reviewed merely because they were packaged. The inventory below separates content review, hash-only reads, and unread material.

**File inventory**

All paths below are relative to this packet, unless they start with `/`. JSON archives were parsed as data. Their embedded source, scripts, command records, exits and outputs were inspected; they were not executed. Binary reads were for hashes, sizes and pair comparisons, not execution or full disassembly.

Content-reviewed packet control files:

- `README.txt`
- `scope.json`
- `tracked.diff`
- `compile-limit/depth40-before.json`
- `compile-limit/depth40.goose`
- `compile-limit/release-verification.json`

Content-reviewed changed files (all files in scope, including untracked files):

- `candidate/docs/wasm/evidence/inline-arrays.md`
- `candidate/docs/wasm/evidence/inline-arrays/after.json`
- `candidate/docs/wasm/evidence/inline-arrays/before.json`
- `candidate/docs/wasm/evidence/inline-arrays/compatibility-summary.json`
- `candidate/docs/wasm/evidence/inline-arrays/compiler-identities.json`
- `candidate/docs/wasm/evidence/inline-arrays/equality-after.json`
- `candidate/docs/wasm/evidence/inline-arrays/equality-before.json`
- `candidate/docs/wasm/evidence/inline-arrays/equality-validation.json`
- `candidate/docs/wasm/evidence/inline-arrays/module-sizes.json`
- `candidate/docs/wasm/evidence/inline-arrays/prior-wasm-summary.json`
- `candidate/docs/wasm/evidence/inline-arrays/query-validation.json`
- `candidate/docs/wasm/evidence/inline-arrays/source-manifest.json`
- `candidate/docs/wasm/evidence/inline-arrays/validation.json`
- `candidate/docs/wasm/status.md`
- `candidate/scripts/run_wasm.mjs`
- `candidate/src/wasm_arrays.h`
- `candidate/src/wasm_binary.h`
- `candidate/src/wasm_codegen.h`
- `candidate/test/expected/wasm_array_equality.out`
- `candidate/test/expected/wasm_inline_arrays.out`
- `candidate/test/expected/wasm_inline_boundaries.out`
- `candidate/test/expected/wasm_inline_effect_path.out`
- `candidate/test/expected/wasm_inline_limited_path.out`
- `candidate/test/expected/wasm_inline_mixed_references.out`
- `candidate/test/expected/wasm_inline_nested_path.out`
- `candidate/test/expected/wasm_inline_optional_references.out`
- `candidate/test/expected/wasm_inline_reference_path.out`
- `candidate/test/wasm/wasm_array_equality.goose`
- `candidate/test/wasm/wasm_inline_arrays.goose`
- `candidate/test/wasm/wasm_inline_boundaries.goose`
- `candidate/test/wasm/wasm_inline_effect_path.goose`
- `candidate/test/wasm/wasm_inline_limited_path.goose`
- `candidate/test/wasm/wasm_inline_mixed_references.goose`
- `candidate/test/wasm/wasm_inline_nested_path.goose`
- `candidate/test/wasm/wasm_inline_optional_references.goose`
- `candidate/test/wasm/wasm_inline_reference_path.goose`
- `candidate/test/wasm_backend.py`
- `candidate/test/wasm_binary.cpp`
- `candidate/test/wasmtime_host.py`

Content-reviewed related files:

- `candidate/src/value_layout.h`
- `candidate/src/wasm_memory.h`
- `candidate/src/wasm_storage.h`
- `candidate/test/wasm_multimemory.mjs`
- `candidate/test/wasm/wasm_ordered_array_cleanup.goose`
- `candidate/test/expected/wasm_ordered_array_cleanup.out`
- `candidate/test/codegen/for_element_walks.goose`
- `candidate/test/codegen/for_repointed_walks.goose`
- `candidate/test/expected/for_element_walks.out`
- `candidate/test/expected/for_repointed_walks.out`

Related files inspected in part:

- `candidate/src/codegen_values.h`: IndexLoc, GenLoc, IsCtl, OperandT, GenOperandVal, HasStmts and equality sections; related searches.
- `candidate/src/codegen_nodes.h`: Binary::CgX and array ForLoop::CgStmt sections; related searches.
- `candidate/src/codegen_types.h`: BitwiseEq, ScalarEq, EqScalars and EqX; related searches.
- `candidate/src/typecheck_exprs.h`: HoldForSequence, CheckBinaryResult and numeric comparison sections; related searches.
- `candidate/src/builtins.h`: cap receiver definition.
- `candidate/src/typecheck_builtins.h`: targeted searches only.
- `candidate/src/typecheck_nodes.h`: targeted searches only.
- `candidate/src/codegen_stmts.h`: targeted searches only.
- `candidate/src/codegen_builtins.h`: targeted searches only.
- `candidate/src/codegen.h`: declaration searches only.
- `candidate/src/ast.h`: targeted searches only.

Other source files read for manifest hashing only, without a semantic review:

- `candidate/src/bce.h`
- `candidate/src/blessed.txt`
- `candidate/src/build.h`
- `candidate/src/buildfile.h`
- `candidate/src/builtin.h`
- `candidate/src/clone.h`
- `candidate/src/codegen_calls.h`
- `candidate/src/codegen_construct.h`
- `candidate/src/codegen_emit.h`
- `candidate/src/codegen_frames.h`
- `candidate/src/codegen_render.h`
- `candidate/src/codegen_stacks.h`
- `candidate/src/data_stacks.h`
- `candidate/src/dump.h`
- `candidate/src/expansion_bind.h`
- `candidate/src/flat_map.h`
- `candidate/src/format.h`
- `candidate/src/gfx.h`
- `candidate/src/gfx_blob.h`
- `candidate/src/goose.manifest`
- `candidate/src/goose.rc`
- `candidate/src/includes.h`
- `candidate/src/jit.h`
- `candidate/src/jit_runtime.c`
- `candidate/src/jit_runtime.h`
- `candidate/src/json.h`
- `candidate/src/lexer.h`
- `candidate/src/lsp.h`
- `candidate/src/lsp_analysis.h`
- `candidate/src/lsp_features.h`
- `candidate/src/lsp_rpc.h`
- `candidate/src/lsp_workspace.h`
- `candidate/src/main.cpp`
- `candidate/src/native.h`
- `candidate/src/optimize.h`
- `candidate/src/optimize_basecase.h`
- `candidate/src/optimize_loops.h`
- `candidate/src/optimize_reassoc.h`
- `candidate/src/optimize_tre.h`
- `candidate/src/packages.h`
- `candidate/src/parser.h`
- `candidate/src/process.cpp`
- `candidate/src/process.h`
- `candidate/src/progress.cpp`
- `candidate/src/progress.h`
- `candidate/src/resolve.h`
- `candidate/src/runtime/goose.h`
- `candidate/src/runtime/jit_c.h`
- `candidate/src/runtime/runtime.h`
- `candidate/src/runtime/runtime_ext.h`
- `candidate/src/runtime/runtime_impl.h`
- `candidate/src/runtime/runtime_os.h`
- `candidate/src/runtime/runtime_threads.h`
- `candidate/src/runtime_inline.h`
- `candidate/src/shaderc.c`
- `candidate/src/shaderc.h`
- `candidate/src/small_vector.h`
- `candidate/src/toolchain.h`
- `candidate/src/type_queries.h`
- `candidate/src/typecheck.h`
- `candidate/src/typecheck_calls.h`
- `candidate/src/typecheck_expansion.h`
- `candidate/src/typecheck_flow.h`
- `candidate/src/typecheck_types.h`
- `candidate/src/utils.h`
- `candidate/src/version.cpp`

Preserved executable files read for size and SHA256 only (symlink targets were read):

- `compiler-data_stacks` -> `/home/dev/Projects/goose-wasm-backend/build/goose-data-stacks`.
- `compiler-native_reference` -> `/home/dev/Projects/goose-wasm-backend/build/goose-shared-services`.
- `compiler-initial_inline` -> `/tmp/goose-wasm-inline-arrays-20261107/build-check/goose-before-followup`.
- `compiler-path_repair` -> `/tmp/goose-wasm-inline-arrays-20261107/repair/goose-after-review`.
- `compiler-query_repair` -> `/tmp/goose-wasm-inline-arrays-20261107/equality-before/goose-before-equality`.
- `compiler-current` -> `/tmp/goose-wasm-inline-arrays-20261107/equality-repair/goose-after-review`.

Module files read for hashing, size or byte comparison:

- `modules/after/equality-O0.wasm`
- `modules/after/equality-O2.wasm`
- `modules/before/equality-O0.wasm`
- `modules/before/equality-O2.wasm`
- `modules/before/unary-O0.wasm`
- `modules/before/unary-O2.wasm`
- `saved-modules/equivalence/wasm_array_iteration-O0-after.wasm`
- `saved-modules/equivalence/wasm_array_iteration-O0-before.wasm`
- `saved-modules/equivalence/wasm_array_iteration-O2-after.wasm`
- `saved-modules/equivalence/wasm_array_iteration-O2-before.wasm`
- `saved-modules/equivalence/wasm_array_shrink-O0-after.wasm`
- `saved-modules/equivalence/wasm_array_shrink-O0-before.wasm`
- `saved-modules/equivalence/wasm_array_shrink-O2-after.wasm`
- `saved-modules/equivalence/wasm_array_shrink-O2-before.wasm`
- `saved-modules/equivalence/wasm_array_widths-O0-after.wasm`
- `saved-modules/equivalence/wasm_array_widths-O0-before.wasm`
- `saved-modules/equivalence/wasm_array_widths-O2-after.wasm`
- `saved-modules/equivalence/wasm_array_widths-O2-before.wasm`
- `saved-modules/equivalence/wasm_control-O0-after.wasm`
- `saved-modules/equivalence/wasm_control-O0-before.wasm`
- `saved-modules/equivalence/wasm_control-O2-after.wasm`
- `saved-modules/equivalence/wasm_control-O2-before.wasm`
- `saved-modules/equivalence/wasm_conversion_boundaries-O0-after.wasm`
- `saved-modules/equivalence/wasm_conversion_boundaries-O0-before.wasm`
- `saved-modules/equivalence/wasm_conversion_boundaries-O2-after.wasm`
- `saved-modules/equivalence/wasm_conversion_boundaries-O2-before.wasm`
- `saved-modules/equivalence/wasm_conversion_global-O0-after.wasm`
- `saved-modules/equivalence/wasm_conversion_global-O0-before.wasm`
- `saved-modules/equivalence/wasm_conversion_global-O2-after.wasm`
- `saved-modules/equivalence/wasm_conversion_global-O2-before.wasm`
- `saved-modules/equivalence/wasm_entry_stack_base-O0-after.wasm`
- `saved-modules/equivalence/wasm_entry_stack_base-O0-before.wasm`
- `saved-modules/equivalence/wasm_entry_stack_base-O2-after.wasm`
- `saved-modules/equivalence/wasm_entry_stack_base-O2-before.wasm`
- `saved-modules/equivalence/wasm_frames-O0-after.wasm`
- `saved-modules/equivalence/wasm_frames-O0-before.wasm`
- `saved-modules/equivalence/wasm_frames-O2-after.wasm`
- `saved-modules/equivalence/wasm_frames-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_arrays-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_arrays-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_arrays-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_arrays-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_boundaries-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_boundaries-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_boundaries-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_boundaries-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_effect_path-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_effect_path-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_effect_path-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_effect_path-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_limited_path-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_limited_path-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_limited_path-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_limited_path-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_mixed_references-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_mixed_references-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_mixed_references-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_mixed_references-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_nested_path-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_nested_path-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_nested_path-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_nested_path-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_optional_references-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_optional_references-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_optional_references-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_optional_references-O2-before.wasm`
- `saved-modules/equivalence/wasm_inline_reference_path-O0-after.wasm`
- `saved-modules/equivalence/wasm_inline_reference_path-O0-before.wasm`
- `saved-modules/equivalence/wasm_inline_reference_path-O2-after.wasm`
- `saved-modules/equivalence/wasm_inline_reference_path-O2-before.wasm`
- `saved-modules/equivalence/wasm_multimemory-O0-after.wasm`
- `saved-modules/equivalence/wasm_multimemory-O0-before.wasm`
- `saved-modules/equivalence/wasm_multimemory-O2-after.wasm`
- `saved-modules/equivalence/wasm_multimemory-O2-before.wasm`
- `saved-modules/equivalence/wasm_no_data_owner-O0-after.wasm`
- `saved-modules/equivalence/wasm_no_data_owner-O0-before.wasm`
- `saved-modules/equivalence/wasm_no_data_owner-O2-after.wasm`
- `saved-modules/equivalence/wasm_no_data_owner-O2-before.wasm`
- `saved-modules/equivalence/wasm_optional_reference_iteration-O0-after.wasm`
- `saved-modules/equivalence/wasm_optional_reference_iteration-O0-before.wasm`
- `saved-modules/equivalence/wasm_optional_reference_iteration-O2-after.wasm`
- `saved-modules/equivalence/wasm_optional_reference_iteration-O2-before.wasm`
- `saved-modules/equivalence/wasm_ordered_array_cleanup-O0-after.wasm`
- `saved-modules/equivalence/wasm_ordered_array_cleanup-O0-before.wasm`
- `saved-modules/equivalence/wasm_ordered_array_cleanup-O2-after.wasm`
- `saved-modules/equivalence/wasm_ordered_array_cleanup-O2-before.wasm`
- `saved-modules/equivalence/wasm_reference_identity-O0-after.wasm`
- `saved-modules/equivalence/wasm_reference_identity-O0-before.wasm`
- `saved-modules/equivalence/wasm_reference_identity-O2-after.wasm`
- `saved-modules/equivalence/wasm_reference_identity-O2-before.wasm`
- `saved-modules/equivalence/wasm_reference_iteration-O0-after.wasm`
- `saved-modules/equivalence/wasm_reference_iteration-O0-before.wasm`
- `saved-modules/equivalence/wasm_reference_iteration-O2-after.wasm`
- `saved-modules/equivalence/wasm_reference_iteration-O2-before.wasm`
- `saved-modules/equivalence/wasm_reference_rebind-O0-after.wasm`
- `saved-modules/equivalence/wasm_reference_rebind-O0-before.wasm`
- `saved-modules/equivalence/wasm_reference_rebind-O2-after.wasm`
- `saved-modules/equivalence/wasm_reference_rebind-O2-before.wasm`
- `saved-modules/equivalence/wasm_reference_returns-O0-after.wasm`
- `saved-modules/equivalence/wasm_reference_returns-O0-before.wasm`
- `saved-modules/equivalence/wasm_reference_returns-O2-after.wasm`
- `saved-modules/equivalence/wasm_reference_returns-O2-before.wasm`
- `saved-modules/equivalence/wasm_repoint_iteration-O0-after.wasm`
- `saved-modules/equivalence/wasm_repoint_iteration-O0-before.wasm`
- `saved-modules/equivalence/wasm_repoint_iteration-O2-after.wasm`
- `saved-modules/equivalence/wasm_repoint_iteration-O2-before.wasm`
- `saved-modules/equivalence/wasm_scalars-O0-after.wasm`
- `saved-modules/equivalence/wasm_scalars-O0-before.wasm`
- `saved-modules/equivalence/wasm_scalars-O2-after.wasm`
- `saved-modules/equivalence/wasm_scalars-O2-before.wasm`
- `saved-modules/equivalence/wasm_scoped_data_reuse-O0-after.wasm`
- `saved-modules/equivalence/wasm_scoped_data_reuse-O0-before.wasm`
- `saved-modules/equivalence/wasm_scoped_data_reuse-O2-after.wasm`
- `saved-modules/equivalence/wasm_scoped_data_reuse-O2-before.wasm`
- `saved-modules/equivalence/wasm_tail_values-O0-after.wasm`
- `saved-modules/equivalence/wasm_tail_values-O0-before.wasm`
- `saved-modules/equivalence/wasm_tail_values-O2-after.wasm`
- `saved-modules/equivalence/wasm_tail_values-O2-before.wasm`
- `saved-modules/path-after/boundaries-O0.wasm`
- `saved-modules/path-after/boundaries-O2.wasm`
- `saved-modules/path-after/effect_path-O0.wasm`
- `saved-modules/path-after/effect_path-O2.wasm`
- `saved-modules/path-after/limited_path-O0.wasm`
- `saved-modules/path-after/limited_path-O2.wasm`
- `saved-modules/path-after/nested_path-O0.wasm`
- `saved-modules/path-after/nested_path-O2.wasm`
- `saved-modules/path-after/nullable_mixed-O0.wasm`
- `saved-modules/path-after/nullable_mixed-O2.wasm`
- `saved-modules/path-after/path-O0.wasm`
- `saved-modules/path-after/path-O2.wasm`
- `saved-modules/path-before/boundaries-O0.wasm`
- `saved-modules/path-before/boundaries-O2.wasm`
- `saved-modules/path-before/effect_path-O0.wasm`
- `saved-modules/path-before/effect_path-O2.wasm`
- `saved-modules/path-before/limited_path-O0.wasm`
- `saved-modules/path-before/limited_path-O2.wasm`
- `saved-modules/path-before/nested_path-O0.wasm`
- `saved-modules/path-before/nested_path-O2.wasm`
- `saved-modules/path-before/nullable_mixed-O0.wasm`
- `saved-modules/path-before/nullable_mixed-O2.wasm`
- `saved-modules/path-before/path-O0.wasm`
- `saved-modules/path-before/path-O2.wasm`

Supplied candidate files not content-reviewed or hashed in this review:

- `candidate/docs/goose_spec.md`
- `candidate/docs/implementation.md`
- `candidate/docs/reference.md`
- `candidate/test/data_stacks.cpp`
- `candidate/test/expected/wasm_array_iteration.out`
- `candidate/test/expected/wasm_array_shrink.out`
- `candidate/test/expected/wasm_array_widths.out`
- `candidate/test/expected/wasm_control.out`
- `candidate/test/expected/wasm_conversion_boundaries.out`
- `candidate/test/expected/wasm_conversion_global.out`
- `candidate/test/expected/wasm_entry_stack_base.out`
- `candidate/test/expected/wasm_frames.out`
- `candidate/test/expected/wasm_multimemory.out`
- `candidate/test/expected/wasm_no_data_owner.out`
- `candidate/test/expected/wasm_optional_reference_iteration.out`
- `candidate/test/expected/wasm_reference_identity.out`
- `candidate/test/expected/wasm_reference_iteration.out`
- `candidate/test/expected/wasm_reference_rebind.out`
- `candidate/test/expected/wasm_reference_returns.out`
- `candidate/test/expected/wasm_repoint_iteration.out`
- `candidate/test/expected/wasm_scalars.out`
- `candidate/test/expected/wasm_scoped_data_reuse.out`
- `candidate/test/expected/wasm_tail_values.out`
- `candidate/test/run_tests.py`
- `candidate/test/wasm/wasm_array_iteration.goose`
- `candidate/test/wasm/wasm_array_shrink.goose`
- `candidate/test/wasm/wasm_array_widths.goose`
- `candidate/test/wasm/wasm_control.goose`
- `candidate/test/wasm/wasm_conversion_boundaries.goose`
- `candidate/test/wasm/wasm_conversion_global.goose`
- `candidate/test/wasm/wasm_entry_stack_base.goose`
- `candidate/test/wasm/wasm_frames.goose`
- `candidate/test/wasm/wasm_multimemory.goose`
- `candidate/test/wasm/wasm_no_data_owner.goose`
- `candidate/test/wasm/wasm_optional_reference_iteration.goose`
- `candidate/test/wasm/wasm_reference_identity.goose`
- `candidate/test/wasm/wasm_reference_iteration.goose`
- `candidate/test/wasm/wasm_reference_rebind.goose`
- `candidate/test/wasm/wasm_reference_returns.goose`
- `candidate/test/wasm/wasm_repoint_iteration.goose`
- `candidate/test/wasm/wasm_scalars.goose`
- `candidate/test/wasm/wasm_scoped_data_reuse.goose`
- `candidate/test/wasm/wasm_tail_values.goose`
- `candidate/test/wasm_memory.cpp`
- `candidate/test/wasm_memory.mjs`
- `candidate/test/wasm_memory.py`
- `candidate/test/wasm_runtime.mjs`

`compile-limit/source-manifest.json` was listed but not independently inspected. The before executable and source identities were checked against the explicit depth-40 record instead. Baseline Git objects were read only for the eight tracked diff blob IDs and the seven unchanged-file comparisons described above.
