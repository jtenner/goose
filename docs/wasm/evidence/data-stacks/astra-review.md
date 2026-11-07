Independent source review of the frozen Wasm Stage C packet

Review date: 2026-11-07. Packet: `/tmp/goose-wasm-stage-c-review-20261107`. Baseline: `0f9978ea908d4614a4b17fefa4bda8132909ce8d`. No PR exists.

**Result.** I found no confirmed new defect in the reviewed snapshot. This is a source review, not a passing validation of the exact candidate. The entry-call change and current harness have no complete rebuilt result in the packet. Performance, allocation, and physical-memory claims remain unmeasured for Stage C.

I read README.txt, scope.json, tracked.diff, and every changed file. All 38 changed-file hashes match scope.json. I used only the frozen packet for the assessment. I ran no compiler, build, test, benchmark, capture, or other resource job. I invoked no other agent or model. I made no production-source changes. File reads and hash comparisons were the only checks performed. This report is the only file I wrote. Prior review conclusions were not used as evidence.

**Confirmed defects.** None found in the current source. This does not establish that all valid inputs work. The review was limited to the admitted subset and the source and evidence listed below.

The saved entry failure is a confirmed defect of the pre-fix compiler, not a new finding against this snapshot. The valid source is present in `evidence/entry-before/entry-call.goose` and `candidate/test/wasm/wasm_entry_stack_base.goose`. Native O0 and O2 both return `7\n7\n`. Wasm O0 emission succeeds but validation fails with “expected i32 but nothing on stack” at offset 0x406. Wasm O2 validates and returns the native output. The current change at `candidate/src/wasm_codegen.h:833` supplies zero as the hidden entry base when required. Its source logic agrees with the signature rule at line 808 and the direct-call rule at line 501. The same check has not passed on a rebuilt candidate in the saved evidence.

**Unverified risks and validation gaps.** These are not claims of reproduced code defects.

1. **High validation risk: the exact candidate is not validated.** Location: `candidate/src/wasm_codegen.h:833`; regression selection: `candidate/test/wasm_backend.py:85`. Valid scenario: a global initializer holds a local growable array and calls `main`, while `_start` later calls the same specialization at base zero. The saved native run proves this input is valid. Conflicting incoming bases make `main` take a hidden i32 parameter. The old failure is recorded, and the new source supplies the parameter, but no post-fix compile, validation, or execution is saved. Impact: module validity and entry cleanup are still unproved for this exact source. Narrow next check: rebuild the frozen source, record the resulting compiler hash, run this same fixture at O0/O2 under both engines, and run the completion-state check. Then run the required suites with that same executable. No further code change is justified by this gap alone.

2. **Medium coverage risk: ordered data cleanup has little direct exit-path evidence.** Locations: `candidate/src/wasm_codegen.h:265`, `candidate/src/wasm_storage.h:43`, and `candidate/src/wasm_arrays.h:49`. Valid scenario: local scalar-array owners and reached defers share a block; exits occur through normal completion, return, break, or continue. A deferred body can also declare a temporary owner or call a function that needs a data stack. The language permits these cases within the defer restrictions. The source uses one reverse-ordered action list, and the planner gives deferred bodies conservative indices above the registering block's owners. That design is consistent on inspection. The changed array fixture exercises one normal-exit defer, while other completion checks inspect final stack tops. Those checks do not establish the full ordering across the other exits. Impact if a defect exists: early reuse, a wrong value read by a defer, or a retained top. Narrow next tests: record native output for interleaved owner/defer cases on each permitted exit, assert that output under Wasm, and inspect each owner top after completion. Include a function called at two stack bases and a deferred body with its own owner. Check the failure reason and validity of each proposed fixture before changing production code.

**Correctness and safety assessment.**

The storage pass assigns lexical indices to owners, restores the next index at block exit, and reserves a distinct persistent range for globals. The shared call-bound solver rejects recursive edges with a nonzero live-stack offset. The base worklist moves each reachable function from unknown to a concrete base and, at most once more, to a dynamic base. Direct calls use the caller's free-stack offset; the extra parameter follows the user parameters. The entry fix closes the observed special-entry mismatch. No additional call-ABI mismatch was found.

The current subset has one live resizable owner per assigned data memory. Owner headers remain in Memory 0. Header references use i32 values, and stored owner references still occupy 16 bytes. Ordinary stored references occupy 8 bytes. A live array interface enables packed ordinary references even when no actual data memory is needed. This avoids making reference types depend only on the number of memories.

Reservations add sizes in i64, check the exclusive end before narrowing, grow before publishing the top, and retain offsets. Valid offsets start above zero. Dynamic access checks the memory identity and uses fixed-index memory instructions. Element addressing preserves the high identity bits and checks the computed low offset. Loads and stores use the declared scalar widths and unaligned accesses. Scope restoration resets tops; it does not shrink Wasm memories.

These helpers are not a complete object-bounds or provenance system by themselves. They rely on the checked frontend, index checks or BCE proofs, and the admitted constructors. Arbitrary forged packed addresses, host writes into exported memories, or a host call to a test-only restore export are not valid Goose counterexamples. I did not report these as defects. The frontend's restrictions on shrinking while references remain live also exclude such invalid triggering cases.

Push captures the owner header before argument evaluation and reads its current length after argument effects. Native RecvLoc captures a mutable receiver for the same reason. Index lowering captures the length before evaluating an effectful index; the admitted owner's base remains stable. Reference-array stores retain the pointee address, and reference-element iteration loads the stored reference instead of returning the element slot. Mutable identifier references are read again at each iteration test. Other expressions are evaluated once, consistent with native temporary-location lowering in the inspected forms. The frontend rewrites generic scalar `.=` to ordinary assignment; that case is not an uncovered reference-store error.

Array-valued temporary results, by-value array parameters/results, and unsupported compound layouts fail before the driver writes a module. This avoids pretending that destination lifetime support is complete. Returned scalar values are saved before cleanup. Reached defers and local-owner restores run in reverse registration order. Traps abort the instance, which agrees with the stated defer limits.

**Saved evidence and identity.**

- `previous-coverage` records a successful build, 138 Wasm checks, the native baseline suite, and 52 exact output/diagnostic comparisons. `final-coverage` records 157 Wasm checks and the native baseline suite. Both manifests identify compiler SHA256 `959d31ea4949ae52f74e09e5ea5c8445036e8e928f3f4375b91c4c911c19e2c5`.
- Both source manifests identify the old `src/wasm_codegen.h` as `5ae1b34bdfc98151c3d799671823f06602d12e9b4c85ab39fc03664bf965fee5`. The current file is `bb980f669c459b36dffb2c22d545fab8c6b0387be60faeeed77792dcd2147734`. Reversing only the entry-call edit in memory reproduces the recorded old hash exactly. All other source-manifest files present in candidate match. Four cmake files named by the manifests are absent from the packet.
- The current `test/wasm_backend.py` hash differs from the final run's recorded harness hash. Removing the entry-completion fixture selection alone does not recover the old hash. The old harness text is not included, so I cannot reconstruct every harness difference. The six other recorded helper/adapter files match their final-coverage hashes. The present final-coverage fixtures match; the new entry fixture is absent from that manifest. The previous-coverage no-data-owner fixture has an older hash.
- The compiler binary, emitted modules, compatibility `summary.json`, individual compatibility output files, and old harness source are not archived here. I cannot independently hash that executable or confirm the reference compiler identity used for the 52 comparisons. The 52 result is supported by the saved process log and the current harness design, not by a fresh comparison in this review.
- The entry check script records individual exits but its own process can exit zero after a failing validation. I used the per-command records and stderr, not the wrapper's zero exit, to identify the O0 failure.
- Native logs explicitly skip unavailable device/layer tests, huge-page and Windows commit-limit checks, and unsupported JIT cases. “Baseline suite passed” retains those limits. The build stderr contains warnings, including an enum/non-enum conditional in Wasm code; the saved build exits zero. No warning was treated as a proven runtime defect.
- The saved lease records say that owned child jobs were reaped and the lock released. They are test records, not timing samples or proof of an exclusive benchmark environment.

**Harness quality.**

The differential runner checks native expected output before comparing Wasm, validates modules independently, and uses O0/O2 plus Node and optional Wasmtime. Failure tests require a matching reason and no partial printed line. The unsupported array-result tests first establish a native output and then require a destination diagnostic and no output file. The memory limit fixture keeps 65 owners live and checks the target-specific limit. The helper tests use production emitter/runtime code, separate memories, scalar widths, signed loads, unaligned offsets, invalid selectors, address overflow, and a derived module with a real growth limit. They inspect the top and contents after the failing call returns.

The completion harness inspects exported owner tops after synchronous `_start` return. The repeated-scope test observes the final memory capacity after 20 iterations in one instance; it does not infer reuse from fresh instances or old addresses. These are useful checks. They are not measurements of physical memory, allocations, or performance. The post-run pending-print count is cleared by the host's `finally`; it is not independent proof against a print-buffer leak during execution. The separate print callback test checks that state before `_start` ends. The aggregate number of checks is not a count of distinct language behaviors.

**Runtime, code size, compiler cost, and memory.**

No Stage C runtime or emitted-code-size gain is established by this packet. The earlier scalar converter measurements mentioned in documentation concern another change and are not evidence for data stacks. The saved compatibility log reports unchanged bytes for nine scalar fixtures at two optimization levels, but the individual files and summary are absent. The new array inputs were unsupported by the scalar baseline, so there is no same-input array speedup or size reduction to calculate against that baseline.

Visible costs and limits are:

- `wasm_codegen.h:43` makes ordinary reference values i64 across the module when an array interface is live. `Load` and `Store` then use shared dispatch helpers, including for ordinary Memory 0 pointees. Scalar callers in mixed programs can therefore incur extra work. No dispatch timing or architecture comparison is saved.
- `wasm_arrays.h:74` emits a reservation and store for each literal element and each push. The guest fast path is constant work per push, apart from engine growth costs. It does not copy existing elements. Known-memory element accesses still form a packed address before narrowing for the fixed-index access. Repeated loop tests load length and compute element offsets. No measured benefit from removing that work is shown.
- `wasm_memory.h:117` emits one shared access helper per used opcode, with a case for each memory. Helper code grows with memory count times used opcode count, rather than per access site. Dynamic reserve/top helpers also grow with the memory count. The 64-data-memory limit bounds this dimension, but it does not establish small emitted code or low engine compile time.
- `wasm_binary.h:121` gives every data memory an initial 64 KiB page. At the limit, the 64 data memories alone expose 4 MiB initially, plus Memory 0. Peak capacities remain after top restoration. This is addressable memory, not resident or committed physical memory. Engine reservations and metadata can cost more and are not measured here.
- The planner adds maps, sets, vectors, call edges, and an AST walk. Its base propagation has at most two state changes per function. Cleanup copies action lists at emitted exits and emits deferred bodies at each required exit. Compiler allocation count, CPU time, peak RSS, and larger-program scaling have no samples. The source does not justify a claim of zero allocations or a minimal compiler footprint.
- Locals and temporary values increase emitted local count. Address-taken slots and array headers occupy the function's Memory 0 frame, with no slot reuse inside that frame. Saved top locals are ordinary Wasm locals, not new guest heap allocations on each loop iteration. Engine register allocation, spills, native code size, and physical memory use remain unknown.

The available runtime evidence is Linux x86-64 with Node 24.22.2 and Wasmtime Python 49.0.0. There is no native ARM, macOS, or Windows runtime evidence, no cross-platform build result for the new source, no raw Stage C timing samples, and no compiler-allocation data. No cross-compilation or emulation result was treated as native measurement. A later permitted measurement should freeze the source and executable identity, retain raw samples and controls, and include mixed scalar/array callers, known and dynamic bases, several memory counts, and repeated growth/reuse. This review starts no such job.

**Coverage record.** Paths below are relative to candidate unless they start with evidence. A full read does not mean every possible path was proved. Only the named ranges and topics of supporting files were inspected. Full frontend, native-runtime, and optimizer coverage is not claimed.

Full changed-file reads and hash checks:

- `CMakeLists.txt`
- `docs/design/native-wasm.md`
- `docs/wasm/evidence/data-stacks.md`
- `docs/wasm/status.md`
- `scripts/run_wasm.mjs`
- `src/main.cpp`
- `src/wasm_arrays.h`
- `src/wasm_binary.h`
- `src/wasm_codegen.h`
- `src/wasm_memory.h`
- `src/wasm_storage.h`
- `test/backend_shared.py`
- `test/expected/wasm_array_iteration.out`
- `test/expected/wasm_array_shrink.out`
- `test/expected/wasm_array_widths.out`
- `test/expected/wasm_entry_stack_base.out`
- `test/expected/wasm_multimemory.out`
- `test/expected/wasm_no_data_owner.out`
- `test/expected/wasm_optional_reference_iteration.out`
- `test/expected/wasm_reference_iteration.out`
- `test/expected/wasm_repoint_iteration.out`
- `test/expected/wasm_scoped_data_reuse.out`
- `test/wasm/wasm_array_iteration.goose`
- `test/wasm/wasm_array_shrink.goose`
- `test/wasm/wasm_array_widths.goose`
- `test/wasm/wasm_entry_stack_base.goose`
- `test/wasm/wasm_multimemory.goose`
- `test/wasm/wasm_no_data_owner.goose`
- `test/wasm/wasm_optional_reference_iteration.goose`
- `test/wasm/wasm_reference_iteration.goose`
- `test/wasm/wasm_repoint_iteration.goose`
- `test/wasm/wasm_scoped_data_reuse.goose`
- `test/wasm_backend.py`
- `test/wasm_memory.cpp`
- `test/wasm_memory.mjs`
- `test/wasm_memory.py`
- `test/wasm_multimemory.mjs`
- `test/wasmtime_host.py`

Other full reads:

- `src/data_stacks.h`
- `src/value_layout.h`
- `test/data_stacks.cpp`
- `test/wasm_binary.cpp`
- `test/wasm_runtime.mjs`

Supporting files inspected in part:

- `docs/goose_spec.md`: stack invariant; reference creation and rebinding; reference destinations; array iteration; defer rules.
- `src/codegen_builtins.h`: receiver capture, push and its result, pop, clear.
- `src/codegen_frames.h`: NoteLen, scope restore and defer registration/emission, stack allocation.
- `src/codegen_nodes.h`: scalar/reference reads and unary address expressions; array and range iteration.
- `src/codegen_values.h`: local storage and snapshots; index locations; GenLoc; GenRefVal; related searches.
- `src/typecheck_builtins.h`: array shrink restrictions and element argument checks.
- `src/typecheck_flow.h`: CheckFor and reference-element binding; generic assignment rewrite search.
- `src/typecheck_nodes.h`: identifier reference loads and Unary::Check.
- `src/optimize.h`: Unary::Opt and related reference-expression searches.

Search results only, not substantive whole-file review:

- `src/codegen.h`
- `src/codegen_calls.h`
- `src/codegen_construct.h`
- `src/codegen_emit.h`
- `src/codegen_render.h`
- `src/codegen_stacks.h`
- `src/codegen_stmts.h`
- `src/codegen_types.h`
- `src/typecheck_exprs.h`

Packet control files read: `README.txt`, `scope.json`, and `tracked.diff`. All evidence files were read as text; both source manifests were also parsed and compared with the candidate hashes. Evidence inventory:

- `evidence/entry-before/before-O0-native-build.exit`
- `evidence/entry-before/before-O0-native-build.stderr`
- `evidence/entry-before/before-O0-native-build.stdout`
- `evidence/entry-before/before-O0-native-emit.exit`
- `evidence/entry-before/before-O0-native-emit.stderr`
- `evidence/entry-before/before-O0-native-emit.stdout`
- `evidence/entry-before/before-O0-native-run.exit`
- `evidence/entry-before/before-O0-native-run.stderr`
- `evidence/entry-before/before-O0-native-run.stdout`
- `evidence/entry-before/before-O0-validate.exit`
- `evidence/entry-before/before-O0-validate.stderr`
- `evidence/entry-before/before-O0-validate.stdout`
- `evidence/entry-before/before-O0-wasm-emit.exit`
- `evidence/entry-before/before-O0-wasm-emit.stderr`
- `evidence/entry-before/before-O0-wasm-emit.stdout`
- `evidence/entry-before/before-O2-native-build.exit`
- `evidence/entry-before/before-O2-native-build.stderr`
- `evidence/entry-before/before-O2-native-build.stdout`
- `evidence/entry-before/before-O2-native-emit.exit`
- `evidence/entry-before/before-O2-native-emit.stderr`
- `evidence/entry-before/before-O2-native-emit.stdout`
- `evidence/entry-before/before-O2-native-run.exit`
- `evidence/entry-before/before-O2-native-run.stderr`
- `evidence/entry-before/before-O2-native-run.stdout`
- `evidence/entry-before/before-O2-node.exit`
- `evidence/entry-before/before-O2-node.stderr`
- `evidence/entry-before/before-O2-node.stdout`
- `evidence/entry-before/before-O2-validate.exit`
- `evidence/entry-before/before-O2-validate.stderr`
- `evidence/entry-before/before-O2-validate.stdout`
- `evidence/entry-before/before-O2-wasm-emit.exit`
- `evidence/entry-before/before-O2-wasm-emit.stderr`
- `evidence/entry-before/before-O2-wasm-emit.stdout`
- `evidence/entry-before/check.py`
- `evidence/entry-before/entry-call.exit`
- `evidence/entry-before/entry-call.goose`
- `evidence/entry-before/entry-call.stderr`
- `evidence/entry-before/entry-call.stdout`
- `evidence/entry-before/lease-run.py`
- `evidence/entry-before/lease.json`
- `evidence/entry-before/results.json`
- `evidence/final-coverage/lease.json`
- `evidence/final-coverage/native.exit`
- `evidence/final-coverage/native.stderr`
- `evidence/final-coverage/native.stdout`
- `evidence/final-coverage/source-manifest.json`
- `evidence/final-coverage/validate.py`
- `evidence/final-coverage/wasm.exit`
- `evidence/final-coverage/wasm.stderr`
- `evidence/final-coverage/wasm.stdout`
- `evidence/previous-coverage/build.exit`
- `evidence/previous-coverage/build.stderr`
- `evidence/previous-coverage/build.stdout`
- `evidence/previous-coverage/compatibility.exit`
- `evidence/previous-coverage/compatibility.stderr`
- `evidence/previous-coverage/compatibility.stdout`
- `evidence/previous-coverage/lease.json`
- `evidence/previous-coverage/native.exit`
- `evidence/previous-coverage/native.stderr`
- `evidence/previous-coverage/native.stdout`
- `evidence/previous-coverage/source-manifest.json`
- `evidence/previous-coverage/validate.py`
- `evidence/previous-coverage/wasm.exit`
- `evidence/previous-coverage/wasm.stderr`
- `evidence/previous-coverage/wasm.stdout`

Candidate files not substantively inspected, beyond any source-manifest hash comparison:

- `docs/implementation.md`
- `docs/reference.md`
- `src/ast.h`
- `src/bce.h`
- `src/blessed.txt`
- `src/build.h`
- `src/buildfile.h`
- `src/builtin.h`
- `src/builtins.h`
- `src/clone.h`
- `src/dump.h`
- `src/expansion_bind.h`
- `src/flat_map.h`
- `src/format.h`
- `src/gfx.h`
- `src/gfx_blob.h`
- `src/goose.manifest`
- `src/goose.rc`
- `src/includes.h`
- `src/jit.h`
- `src/jit_runtime.c`
- `src/jit_runtime.h`
- `src/json.h`
- `src/lexer.h`
- `src/lsp.h`
- `src/lsp_analysis.h`
- `src/lsp_features.h`
- `src/lsp_rpc.h`
- `src/lsp_workspace.h`
- `src/native.h`
- `src/optimize_basecase.h`
- `src/optimize_loops.h`
- `src/optimize_reassoc.h`
- `src/optimize_tre.h`
- `src/packages.h`
- `src/parser.h`
- `src/process.cpp`
- `src/process.h`
- `src/progress.cpp`
- `src/progress.h`
- `src/resolve.h`
- `src/runtime/goose.h`
- `src/runtime/jit_c.h`
- `src/runtime/runtime.h`
- `src/runtime/runtime_ext.h`
- `src/runtime/runtime_impl.h`
- `src/runtime/runtime_os.h`
- `src/runtime/runtime_threads.h`
- `src/runtime_inline.h`
- `src/shaderc.c`
- `src/shaderc.h`
- `src/small_vector.h`
- `src/toolchain.h`
- `src/type_queries.h`
- `src/typecheck.h`
- `src/typecheck_calls.h`
- `src/typecheck_expansion.h`
- `src/typecheck_types.h`
- `src/utils.h`
- `src/version.cpp`

Unread or unavailable evidence outside this packet: the old compiler and its complete build configuration; generated C, native binaries, Wasm modules and per-case outputs; the old test harness; the compatibility reference binary and summary; the earlier failing-first records mentioned under `/tmp/goose-wasm-multimemory-20261107`; and performance/measurement or previous-review documents linked from the status page. No prior review was consulted. Unchanged scalar and typing fixtures that the runner references, and `test/run_tests.py`, are also absent from the candidate snapshot. Their saved aggregate results were inspected, but their full cases were not reviewed here.

The parent can use this as a completed source-review report. Exact-snapshot execution validation and performance validation remain incomplete for the reasons above.
