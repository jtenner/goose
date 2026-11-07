Independent read-only review, 7 November 2026

**Assessment.** No confirmed correctness, design, or memory-safety defect was found in this increment. The source and saved results support the stated, limited Memory 0 aggregate-array scope. This is not full-backend acceptance. Compiler cost, guest runtime cost, engine code size, and physical memory use remain unmeasured. Performance acceptance must remain open.

I inspected all 42 review files, consulted all 16 context files, and followed the relevant checked-AST and native construction paths. The inventories below state the scope of inspection. I used no prior review finding as evidence. I did not run a compiler, build, test, debugger, benchmark, Wasm engine, or saved harness. I used no child agent or Claude. All review writes are in this review directory. No production file, test file, or Git index was changed. Read-only Python analysis checked hashes, saved records, and binary section data. These checks are not new execution evidence.

**Identity and preservation.** The worktree is `/home/dev/Projects/goose-wasm-backend`, branch `feat/wasm-multimemory-backend`. HEAD equals baseline `0d64e43d32f17485526beef0d463e9c9abad9102`. The candidate remains a staged, uncommitted diff.

- Packet and independently read staged binary diff SHA-256: `c2288364be3e49dddc40e26e285fc749286ece912ea1efac748f0ab5edb0e7aa`.
- Candidate compiler SHA-256: `bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d`.
- Accepted parent compiler SHA-256: `250902481fe28fadfd7102f7ac64475814c864dbc91ff2060ce5b9ed360eb73c`.
- All 58 worktree files and all 58 packet snapshots match `scope.json`, before and after inspection. Both complete records are identical. All 2,593 archived evidence hashes also match before and after.
- All 4,683 entries in `artifact-hashes.json` match the raw files. All 298 `final-modules.json` entries match saved final binaries.
- All 87 build manifest entries match current files: 86 compiler/build inputs and the fixed-layout test. All 3,849 full-suite test input hashes match. This independently supports `identity-check.json`.
- The build log shows `main.cpp.o` and `version.cpp.o` rebuilt and the compiler linked. The freeze script checked source hashes, copied the executable, and recorded its hash. Later units checked the frozen source and executable identity. I did not reconstruct the compiler or claim a reproducible-build result. Saved build stderr contains warnings; the build exit is zero.

The detailed records are `hash-before.json`, `hash-after.json`, `manifest-audit.json`, `artifact-audit.json`, `behavior-evidence.json`, and `additional-context-hashes.json` in this directory.

**Confirmed findings.** None. There is no verified valid triggering case for a production defect, so no severity or fix request is assigned. No code repair is proposed without failing evidence.

**Correctness and design assessment.**

1. Admission remains a type and operation decision. `src/wasm_support.h:51` permits a nominal element only in a fixed or static-capacity limited array. It still rejects direct nested array elements and data-memory aggregate elements. Reachable fields and reference pointees are checked. Selected variants inspect their selected payload; whole enums inspect all payloads. Root/nonfixed fields, relative references, and owner-reference fields retain their prior guards. `src/wasm_codegen.h:149` requires the fixed proof before it returns an i32 array representation.
2. The cache does not publish provisional success. `WasmValueSupport::Check` gathers the reachable graph in `seen`, checks fixed sizes and positive nominal strides, then inserts all successful types into `validated` at line 92. `TryFixedSize` checks multiplication and prefix addition before caching a size. It checks cached sizes against each requested limit. A successful array size computation also caches its element size, which makes the new `sizes.at(element)` check valid. Reference cycles do not enter stored-size recursion through their pointees. By-value self-containment is rejected by the checker. No type mutation was added after this proof.
3. Fresh construction is bounded. `FreshOwner` establishes planned storage and rejects inline argument bindings. `FixedChild` checks the child image against the parent image and checks both offset additions. `ConstructAggregateArray` checks kind, positive stride, literal count, and fixed extent before it constructs children. Its 64-bit offset arithmetic is bounded by the checked capacity product. Empty structs have a one-byte stride; standalone zero-length arrays keep the existing owner identity convention. Zero-stride variants are not admitted.
4. Construction order matches native lowering. `src/wasm_fixed.h:290` writes a limited array's final checked count first. The loop completes one child's construction or copy before the next initializer. `src/codegen_construct.h:1118` uses the same prefix-before-elements order in `FixedArrayLitAt`; `StructLitAt` follows field order. The saved native global-effects C also writes the temporary array count before the two `inspect` calls. No extra evaluation of an initializer is introduced by child-range checks.
5. The named-owner copy at `src/wasm_fixed.h:304` uses the original stored type, requires exact representation equality, and requires a memory slot. Its source is a nominal owner in Memory 0. Its destination is a checked fresh child. It copies exactly one stride with `memory.copy(0, 0)` and does not modify the source. COPY wrappers are removed only as checked copy nodes. A reference, field, index, or reference-returning call uses the existing `ConstructFixed`/`ResolvePlace`/`CopyFixed` path instead. These paths check exact source layout and evaluate the source place once. Whole-array fresh copies retain the full-image copy path in `InitArrayCopy`; adapted source layouts are rejected through `ActualType`, not merely the adapted expression type.
6. Nested offsets and references preserve their representations. Field offsets come from the shared packed layout. Array indices use the checked stride, captured header/length, and overflow check in `ElementOffset`. Scalar reads and writes use the field's stored width. Ordinary references can be packed i64; inline-array references remain Memory 0 i32. `PlaceAddress` checks an unknown packed memory identity before narrowing a field-array reference. Known frame addresses rely on the reserved frame bound. New aggregate values cannot reach data memories, although scalar arrays can hold references to them or to their inline arrays. This also preserves reference aliasing when an aggregate image is copied.
7. Matches copy selected payloads into planned fresh owners after tag and payload-range checks. Fields and nested inline arrays in those payloads keep their offsets. The new array element path does not add an aggregate value ABI. `LoadElement`, `StoreElement`, and `AssignElement` reject whole aggregate scalar operations. Field and variable assignment guards remain in place.
8. Calls and hidden runtime children retain their guards. Direct signatures use `RequireCallValue`; inline bindings and blocks reject array/aggregate arguments or results; checked callback parameters and results are checked in `BindTree` and `CallValue`. `RunChildren` visits the checked callback body and default initializer. Storage planning also walks those bodies. `ConstructFixed` rejects aggregate-array defaults, including nested field construction; `InitArray` routes direct defaults there before unwrapping a `defaultinit`. Scalar-expression and array-temporary guards prevent unsupported default/copy results from becoming scalar addresses. Existing nominal element defaults still use fixed-value construction; no whole-array default/fill ABI is added.
9. Push, pop, equality, and by-value iteration are explicitly rejected. Direct field-path iteration retains its guard. Existing named/reference-index iteration can capture an index once while reloading mutable reference slots on each pass, as native `IndexLoc` and `ForLoop::CgStmt` require. Reference iteration binds the stored element address, not a scalar aggregate load. Printing an aggregate array still reaches the unsupported printing-layout guard; it is not rendered as an address.
10. Cleanup remains tied to scope and function exits. The new inline owners use the existing activation frame, not data-stack reservations. All frame slots are planned before the function body runs. Return, break, continue, and defer paths use the existing cleanup lists; function exit restores the saved frame top. Calls reserve above live caller storage. Saved callback and cleanup fixtures exercise fixed copies with data owners, nested calls, early return, break, continue, and defer effects. No new trap-unwind guarantee is inferred: these adapters stop an instance on a runtime failure.

**Saved functional evidence checked.**

- I matched all 14 promoted fixture sources to their saved source files and all expected outputs to the native oracle output. I checked 82 targeted Node, Wasmtime, and Node owner runs against those outputs, saved exit status, and empty stderr. There were no mismatches. These include both O0 and O2.
- I checked all 19 operation gates at both levels: 38 target rejections. Their saved native emission, native build, and native run exits are zero. Every target exit is nonzero and has one of its specified reasons. The cases cover fixed/limited defaults, fills including zero count, push, used/discarded pop, iteration by value, equality, element/array replacement, adaptation, data-memory values, direct nested elements, field iteration, direct/inline arguments, array results, and callback arguments. Successful native cases reused from build01 are identified as such; corrected pop uses build02. The final full suite repeats native validity with the frozen candidate.
- Across targeted result manifests, all 466 command records have matching exit files and saved stdout/stderr. This checks record consistency, not that every command succeeded; expected target failures and invalid-input attempts remain failures.
- The original eight native01 families pass on the accepted parent and reach its earlier aggregate-element target guard. The candidate's positive evidence is separate. I did not treat the parent rejection as a candidate defect.
- Product overflow is `536870912 * 8 = 4294967296`. Limited prefix overflow is `4294967292 + 4 = 4294967296`. The frame case combines two `4 + 268435456 * 8` owner images. The test emits native C, then expects the precise Wasm layout/frame failure, and checks that no module was written. All six generated C files are present; no huge-image executable or module is present. Their individual command logs are not retained, so the saved 904-check aggregate success plus the hashed harness and artifacts are the evidence for these final bounds checks. They are compile-only checks, not successful large runtime allocations.
- The saved fixed-layout test reports PASS. Its source checks bounded products/sums, cached limits, recursive reference admission, rejected provisional caches, tag widths, selected variants, aggregate arrays, data/nested-array rejection, and a synthetic zero-stride variant. The last case is a defensive layout test, not language-valid coverage of a fieldless variant element.
- The saved full Wasm log says `wasm backend: 904 checks passed`; stderr is empty and the unit exits zero. The count includes diagnostics, executions, and static controls. It is not 904 independent programs. There is no full per-command audit trail for this suite.
- The saved native baseline reports all tests passed, with GCC 14.2.0, TinyCC, the explicit library path, four workers, and the configured Clang check. Device/platform/JIT skips remain visible. This is Linux native evidence. It proves neither Windows/macOS nor a different CPU architecture. The suite's elapsed summary is not a controlled performance sample.
- I compared all 52 saved native C/report/diagnostic/scalar-Wasm pairs directly, including source hashes and zero exits. The scalar checkpoint identity is `63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`. I also compared all 168 accepted-parent/candidate module pairs, stdout, stderr, and zero exits. They are identical. These are exact output controls, not timing results.
- Eight unit lease/release records were inspected. They record reaped children, an inactive lease, no remaining owned processes, and a successful released nonblocking probe. build01 is an exit-1 setup unit; later final units exit zero. I took no lease and started no workload.

**Damaged modules and ownership controls.** The saved short-copy modules change both seven-byte copies to six. The stride modules change eight element stride constants from seven to eight. I compared these saved WAT changes with the original WAT. Parse/validation exits are zero. At O0 and O2, both engines fail the short-copy test at `control.goose:7` and the stride test at `control.goose:8`, with `assert failed` and no stdout. These are the intended checks, not arbitrary traps.

The long-copy control extends each copy to eight bytes. Its saved modules validate. The Node guard reports `aggregate constructor crossed its planned owner image`, with no accepted output. The unmodified instrumented module prints `control` and exits zero. The guard checks the active frame top and eight sentinel bytes at print completion, before it writes the output. It requires one completion and checks frame-top restoration after return. `wasm_multimemory.mjs` waits for synchronous `_start` completion, then checks frame and data tops and the configured page-growth condition. It does not infer release from old addresses or sleeps. The long-copy neighbor guard and stack-top controls are Node-only; Wasmtime checks output and guest assertions, not that host guard. The copy control covers one small fixed struct owner, not every nested or limited layout.

Saved thin/packed WAT signatures show `arrayref(i32) -> i32` in both modes, and `elementref(i32) -> i32/i64` respectively, at both levels. The ABI control is supported by nested-field, hidden-reference, and alias fixtures. It does not establish arbitrary data-memory aggregate support or test every optional/null path.

**Coverage gaps and unverified risks.** These are not confirmed defects.

- `wasm_aggregate_array_global_effects.goose` reads an earlier initialized global. It checks global effect order and final count, but cannot observe its own not-yet-initialized array count. The failed self-read attempt is language-invalid. Prefix publication order is supported by native and Wasm source inspection, not that fixture alone.
- Direct aggregate-array printing, nested default rejection, and all combinations of callback/default/inline aggregate-array paths do not each have a dedicated new native-valid gate. I found guards in the shared paths. Add focused cases if those paths change. Existing aggregate and array gates are useful but do not replace a complete combination matrix.
- The cache has synthetic recursive-reference and failure tests, but no new targeted stress corpus for deep recursive aggregate-array reference graphs. Static inspection found no provisional-success bypass. Compiler resource behavior for such graphs remains unmeasured.
- Constant-local checks cover direct named owners and simple literal elements. A copied reference, indexed/field source, reference-returning call, or more complex nested initializer can add place/copy temporaries per occurrence through existing helpers. Do not extend the 12/11-local claim to all constructors.
- Small damaged-copy controls do not prove every prefix width, child range, or alias case. The positive fixtures and bounded layout proof provide separate support. The large rejection tests do not execute near-4-GiB memory accesses.
- The full suite preserves aggregate logs and artifacts, not individual successful or failed command streams. I cannot independently reconstruct every assertion result from logs. Targeted units give stronger per-command evidence for their covered cases.

**Performance and memory assessment.** Static parsing of saved binaries confirms the following values at both O0 and O2. Local counts are declared function locals, not register counts or physical memory use.

| Constructor | 32 elements | 256 elements | Main-function locals |
| --- | ---: | ---: | ---: |
| Named owner elements | 1,426 bytes | 5,240 bytes | 12 at both sizes |
| Literal elements | 1,125 bytes | 3,110 bytes | 11 at both sizes |

The corresponding full function-local vectors are `[3,12,1,0]` and `[3,11,1,0]`. Sparse-capacity final modules are 1,182 bytes at capacity 32 and 1,205 bytes at capacity 65,536, with vector `[3,9,2,0]` in both cases. Their Memory 0 minimums are one and nine pages. Thus unused capacity is not serialized into the module, but it still contributes to addressable memory. The footprint table is verified independently in `artifact-audit.json`.

Construction work grows with initializer count, nested fields, and copied bytes. The direct named path adds one bulk copy per element and avoids per-element copy scratch locals. It does not establish a runtime speed gain. Whole-array exact copies still copy the entire fixed image, including the limited count prefix and unused capacity; their byte work is proportional to capacity times stride, not live length. Enum copies include their maximum stored image. No new general aggregate runtime temporary or runtime heap allocator is introduced.

Compiler costs include emitted code and local-vector growth, cached layout/type tables, and the work/seen containers for admission. The successful graph is reused, but rejection and complex source-place paths are not allocation-free. `Call::ValueArgNodes` builds a vector; explicit COPY-wrapper inspection can allocate compiler scratch per wrapper. A wrapper is not a guest heap allocation. These costs need measurements before any allocation claim.

Frames sum planned owner images, including separate copies, match payload owners, and slots in separate lexical branches/scopes. There is no new intra-frame slot reuse. A small live length does not reduce a static limited owner's frame reservation. Memory growth retains pages after stack-top restoration. Sparse globals reserve their full image for instance lifetime. Module size, stack-top restoration, addressable pages, peak RSS, and physically retained memory are different quantities.

The 168 unchanged prior module pairs rule out emitted-byte changes for that corpus. They do not rule out compiler CPU/RSS/allocation regressions from new shared-path checks. There are no controlled compiler CPU, RSS, allocation, guest initialization/execution, engine-code-size, or physical-retention samples for this increment. No runtime gain or minimal physical-memory footprint is established.

The queued handoff at `docs/wasm/measurements.md:94` is concrete and appropriate: compare the accepted enum and candidate compilers on shared controls; use native C from the same frozen source for newly admitted programs; separate compiler, engine initialization, and guest execution phases. It names named/nested 32/256 literals, explicit COPY wrappers, sparse capacities, large unused-capacity copies, matches, nested paths, thin/packed references, callbacks, repeated activations, cleanup, and growth. It asks for raw samples, identities, allocations, RSS, pages, code size, and qualified conclusions under a fresh exclusive lease. Keep these items pending. Before collection, specify workload/harness revisions, host/engine controls, warmups, repetitions, and the decision threshold in that new measurement scope. Prior scalar grants and scalar results cannot establish this increment's costs. The parent cannot run newly admitted programs, so do not invent a same-program parent Wasm timing comparison.

**Input availability and inspection limits.** No required review file, context file, snapshot, compiler identity file, or manifest-listed artifact was missing. All 42 review files were inspected for this change. Context files were consulted in the relevant portions listed below; this is not a full audit of unrelated native compiler, host formatting, or test-runner code. All archived/raw manifest entries were hashed, but not every generated C file or binary received semantic inspection. Selected WAT, native C, command records, outputs, and failure records were inspected as stated above. Individual full-suite command logs, new timing/allocation/RSS samples, and non-Linux/native-architecture evidence were not supplied. Prior review reports and prior conclusions were not used.

**Inspected review-file inventory.** Every row was read. Both its worktree file and packet snapshot passed the before/after hash checks.

| File | Review focus |
| --- | --- |
| `docs/wasm/evidence/fixed-aggregate-arrays.md` | Scope, provenance, claims, limitations |
| `docs/wasm/measurements.md` | Increment measurement handoff and limits of earlier results |
| `docs/wasm/status.md` | New increment claim, scope, and remaining stages; old review conclusions excluded |
| `src/wasm_arrays.h` | All array helpers and new operation guards |
| `src/wasm_codegen.h` | Type admission, shared scalar/call paths, bindings, cleanup, frame planning |
| `src/wasm_fixed.h` | All stored-value helpers, fresh child proof, copies, new constructor, matches |
| `src/wasm_support.h` | Complete admission graph and validated/size caches |
| `test/expected/wasm_aggregate_array_callbacks.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_cleanup.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_control.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_effects.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_enums.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_fields.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_global_effects.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_hidden.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_limited.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_nested_fields.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_packed.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_values.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_walk_packed.out` | Expected output compared with saved native oracle |
| `test/expected/wasm_aggregate_array_walk_thin.out` | Expected output compared with saved native oracle |
| `test/wasm/wasm_aggregate_array_callbacks.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_cleanup.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_control.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_effects.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_enums.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_fields.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_global_effects.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_hidden.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_limited.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_nested_fields.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_packed.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_values.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_walk_packed.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm/wasm_aggregate_array_walk_thin.goose` | Complete fixture; intended assertions and saved native/engine output checked |
| `test/wasm_aggregate_admission.py` | 19 native-valid gates and three compile-only bounds cases |
| `test/wasm_aggregate_checks.py` | Mutation controls, ABI signatures, size and local-count checks |
| `test/wasm_aggregate_guard.mjs` | Live-owner completion guard and top restoration |
| `test/wasm_backend.py` | Full suite control flow and new integration |
| `test/wasm_enum_admission.py` | Data-element rejection change and shared enum gates |
| `test/wasm_fixed_layout.cpp` | Complete synthetic layout/admission checks |
| `test/wasm_struct_admission.py` | Data-element rejection change and shared struct gates |

**Consulted context-file inventory.** All 16 files and their snapshots passed before/after hash checks. Large context files were read at the relevant definitions and callers.

| File | Context consulted |
| --- | --- |
| `src/value_layout.h` | Complete layout service: equality, strides, prefixes, checked sums/products, caches |
| `src/wasm_storage.h` | Complete type discovery, owner/callback/default scans, frame metadata and stack assignment |
| `src/wasm_memory.h` | Complete access/copy/reserve/restore helper implementation |
| `src/wasm_binary.h` | Complete encoding, unaligned memargs, zero reservations, module memory limits |
| `src/data_stacks.h` | Complete call graph bounds and recursive-component rules |
| `src/ast.h` | Array/struct literals, calls and ValueArgNodes, defaults, iteration and declaration metadata |
| `src/codegen_nodes.h` | Native literal routing, match payload copies, array iteration and mutable paths |
| `src/codegen_values.h` | IndexLoc snapshots and stride access; fixed-array literal dispatch and copies |
| `src/codegen_stmts.h` | Native fresh declarations and destination routing |
| `src/typecheck_flow.h` | Array iteration binding, reference decay, global defaults, declaration initialization |
| `scripts/run_wasm.mjs` | Host execution/completion, failures, memory reads, print ownership |
| `test/wasmtime_host.py` | Engine setup, failures, output and pending ownership checks |
| `test/wasm_multimemory.mjs` | Instrumented top exports, completion, growth and restored owner checks |
| `test/backend_shared.py` | Exact-comparison corpus and saved result semantics |
| `test/run_tests.py` | Baseline setup, worker completion, failure aggregation, native/JIT scope |
| `CMakeLists.txt` | Compiler source/header registration and platform build context |

Additional source consulted: `src/clone.h` (`RunChildren`), `src/codegen_construct.h` (`FixedArrayLitAt` and `StructLitAt`), `src/typecheck.h` (zero-size element validity), `src/typecheck_types.h` (defaults and fixed classes), and `src/typecheck_builtins.h` (COPY validity and per-use defaults). Their hashes are saved in `additional-context-hashes.json`.

**Review-side evidence files.**

- `hash-before.json` and `hash-after.json`: per-file worktree/snapshot/archive hashes and staged/compiler identity.
- `manifest-audit.json`: all raw, final-module, build-source, and suite-input hash results.
- `artifact-audit.json`: exact pairs, prior-module pairs, binary-derived static sizes/locals/pages, and command-record consistency.
- `behavior-evidence.json`: all fixture oracle comparisons, 38 native-valid gate results, full targeted control commands/results, and text-mutation checks.
- `additional-context-hashes.json`: additional source identities.
