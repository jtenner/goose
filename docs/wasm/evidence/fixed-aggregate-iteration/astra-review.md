Independent read-only review of the copied fixed aggregate iteration increment, 2026-11-07.

No confirmed correctness or design defect was found in the frozen staged change. The new path implements the stated Memory 0 subset and keeps the existing scalar, reference and by-reference path. The saved functional evidence supports this assessment. Performance acceptance remains open. There are no new runtime, CPU, RSS, allocation, engine-code-size or physical-retention measurements for this increment.

This review used source reading, saved log comparison, hashing, and inspection of saved binary sections. It did not run a compiler, build, test, engine, debugger, benchmark, or supplied harness. It did not acquire or probe a resource lease. It used no child agents or Claude. All review writes are under this report's directory. No production, test, document or Git state was changed.

The reviewed branch is `feat/wasm-multimemory-backend`. Baseline and current HEAD are `fcaba2e02bc6925f8e9c8c759f82d6eced526d21`. The candidate is the staged diff, not a commit. The packet patch and the live `git diff --cached --binary` have SHA-256 `f9129398a1249f51b40722af40f45156cd16bf221465dc2a15c608168af1cf50`. The candidate compiler has SHA-256 `c9519e59d47ea996b84d249fee688704bfab0ed49cf5c1ef844e7daf3bdd60d2`. The exact parent compiler has SHA-256 `bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d`.

The complete per-file hashes are in [identity-before.json](identity-before.json) and [identity-after.json](identity-after.json). All 63 live files and packet snapshots match the scope hashes before and after review. HEAD, branch and staged patch also remain unchanged. The saved build manifest's 86 compiler inputs and full-suite manifest's 3,880 test inputs match the live files. These checks support source and binary provenance; they are not a fresh rebuild or an independent proof of the build process.

The implementation review reached the following conclusions. File and line numbers refer to the frozen snapshots and matching live files.

| Area | Source and reasoning | Assessment |
| --- | --- | --- |
| Exact plan | `wasm_storage.h:104-115` adds a plan only for a nominal binder with `IK_ARRAY`, no explicit byref, and checked `copybind`. The key is `VarDef*`; initialization is the actual loop node. `Build:168-174` records the image and at least one storage byte. | The plan does not invent a by-value call/result ABI or a data-memory owner. |
| Plan use | `wasm_codegen.h:364-372` requires `IterationCopy`, matching initialization, no argument and initialized state. `wasm_arrays.h:700-708` also checks kind, byref, copybind, inline array, nominal element, Memory 0, equal representation type and positive element image. `FreshOwner` checks initialization and image again (`wasm_fixed.h:38-51`). | No unplanned binder is silently accepted. |
| Type and full-range proof | `RequireFixed`, `WasmValueSupport::Check` and `TryFixedSize` bound the image and reject unsupported layouts. With capacity C, prefix P and positive stride D, the array image is P+C*D. Checked construction and retained mutation guards keep current length at most C. The loop requires index < current length before `ElementOffset` and the copy. For a valid array place, the selected image ends within its reserved image. Frame sum and runtime frame-end checks also bound the destination. | The selected place's `bounded=true` relies on an established range proof. It does not rely only on the first-byte overflow check. Invalid host-corrupted lengths are outside the admitted language input. |
| Snapshot and index order | `wasm_arrays.h:720-738` obtains one selected address, copies the complete image, writes the index binder, then enters the body. There is no user callback between the length check and copy. | Writes, clear or rebind in the body cannot change the current copied value. Future passes still use the current source path and count. |
| Source evaluation | `ArrayHeader`, `CaptureArrayWalk` and `LoadArrayWalk` retain one-time call/index effects and the existing reload of mutable reference slots. Effectful indices freeze the parent view before their effects. A selected address is not resolved a second time by `CopyFixed`. | The source expression's effects run once where required. Reloading a mutable reference path on a later pass remains intentional. |
| Storage and lifetime | `Bind:330-348` assigns a separate offset for each distinct binder. `EmitSpec:1038-1059` and global init at 1113-1119 reserve the combined frame before execution and restore it on normal completion. No binder reserve is emitted in `ArrayFor`. | Each activation has its full binder image even on zero trips or an untaken branch. Repeated passes reuse the same slot after body cleanup. Nested and cloned binders have distinct slots. |
| Zero trips and empty identity | The exit branch is before the element address and copy. Empty structs have a one-byte image (`value_layout.h:305-310,369-372`). Empty standalone variants can have a zero image and an identity byte, but arrays of zero-stride variants remain rejected (`wasm_support.h:89-90`). | Empty structs retain independent identities. The new loop does not admit zero-stride variant arrays or copy on zero trips. |
| Readonly and shallow references | `CheckFor:2054-2073,2113-2131` assigns the checked copy binder. `CheckLValue:43-49` makes its contents readonly. `LoadType:742-752` and representation equality preserve the intended const/load distinction. Full-image Memory 0 copy retains stored reference bytes. Thin references load as i32; packed references retain their high memory identity and low offset. | Binder mutation is a frontend rejection. A writable reference field can still modify its original pointee. This is intended shallow-copy behavior. |
| Native agreement | Native `ForLoop::CgStmt:1030-1177,1222-1227` uses the same checked copy classification and `FixedLocal`. `FixedLocal:502-513` constructs a value copy, using scoped storage for large native values. | Native and Wasm have the same selected-value semantics. Their physical storage strategies need not match. |
| Checked bodies and clones | Storage walk handles `defaultinit`, `fvbody`, inline bodies and global initializers. Binding uses `RunChildren`, which visits checked callback/default bodies. `ForLoop::Cp1:1051-1058` creates a new node and remaps the binder; `Remap:694-713` copies binder flags into a new owned variable. | Callback/default/global storage discovery is consistent. Repeated emission of one defer body reuses its checked identity and slot. Separate inline clones get distinct slots. |
| Cleanup and shared paths | Copy is before `BlockValue`; normal body cleanup remains at block completion. Continue, break and return retain `Cleanup` before their existing branch. The non-nominal runtime arm is unchanged. `CopyFixed`, `CopyBytes`, frame reservation, memory dispatch and activation cleanup are unchanged shared helpers. | The increment adds no data-stack lifetime action for the fixed binder. The live inner-cleanup control can observe a missing restore before outer cleanup. |
| Scope exclusions | Type/admission guards still reject nonfixed/root/relative layouts, slices, data-memory aggregate values, direct field-path iteration, array/value call/result ABI, aggregate fills/defaults and whole-value mutation. | Frontend-invalid input and explicit target exclusions are not defects in this increment. |

No confirmed finding requires a severity, triggering program or repair. No unexecuted hypothesis was promoted to a defect. The evidence limits below are separate from correctness findings. There is no requested implementation change from this review.

The saved evidence was checked as follows. [evidence-audit.json](evidence-audit.json) records the stream comparisons and failures; [raw-identity-audit.json](raw-identity-audit.json) and [evidence-hashes.json](evidence-hashes.json) record identity checks. The small review scripts only read saved artifacts.

| Evidence | Independent inspection | Limit |
| --- | --- | --- |
| Packet and archive | Scope read first. All 40 review files inspected. All 2,338 archived evidence hashes, 4,622 raw artifact identities and 360 final module identities match. No listed artifact is missing. | A hash inventory proves file identity, not behavioral coverage. |
| Initial native cases | Read the native harness and all 90 status records. Compared the 11 valid families at O0/O2 with expected output and exact parent target rejection. Inspected the original enum parser diagnostic and the one-line corrected source diff. | The first enum source is invalid. It is not counted as a valid compiler regression. |
| Corrected enum and target | Checked the eight preserved corrected-enum streams/statuses and native summary. Compared all 24 native family/optimization cases with all target Node, Wasmtime and owner output. All 120 target commands have exit 0 and empty stderr. | The build unit overwrote its generic native results/summary with target results. The eight-row native audit is a reconstruction. The original native manifest is unavailable. Individual streams and summary remain. |
| Native-first controls | Read the control/checkpoint/zero fixtures, runner and saved records. The two old live-adapter failures are preserved. The old adapter expected top 17 and payload offset 9. The stored u32 prefix requires top 13 and payload offset 5. | An adapter expectation error is not a production defect. The adapter identity was recorded after the first completed unit, before correction, as its note states. |
| Corrected controls | Read the 54-command continuation and its streams. All damaged modules have successful saved parse/validate records. Both engines report the designated guest assertions: short copy at control line 6; stride at line 5 after one printed iteration; alias at line 8; wrong source memory at packed-reference line 5. | These are 54 commands, including intended nonzero commands, not 54 successful guest runs. |
| Live host controls | Verified the long-copy neighbor sentinel reason, eager-zero binder reason, and missing-inner-restore reason at the first `restored` checkpoint after stdout `inner`. The good cleanup adapter passes on the unchanged prior guest modules at both optimization levels. Source checks current live owner tops and the live outer value at print completion. | Neighbor, zero-trip and live-cleanup controls are Node-only. They do not measure physical memory retention. |
| Full Wasm suite | Read runner integration, saved command, exit 0, empty stderr and `wasm backend: 1034 checks passed`. The 15 new fixtures and controls/limits/footprint are included. | The total counts several kinds of check, not 1,034 independent programs. Full-suite evidence has aggregate logs and artifacts, not a stream for every command. Targeted units give stronger per-command evidence. |
| Native baseline | Read the saved command, final section results, skip statements, exit 0 and empty stderr. It used the frozen compiler, Linux native profile, four jobs and explicit TinyCC library path. | Platform/device and unsupported JIT skips remain. Linux results do not establish execution on another OS or CPU architecture. This was not a new sanitizer run. |
| Exact comparisons | Compared all 52 saved C/Wasm outputs and associated compiler stdout/stderr/exits between reference and candidate, including manifest hashes. | The older scalar reference differs from the exact aggregate-array parent. These are exact-output checks, not speed tests. |
| Accepted parent modules | Compared all 196 parent/candidate module bytes and compiler stdout/stderr/exits directly. All match. | The compatibility script compares compiler emission, not a separate pair of guest executions. Exact module identity does not measure compiler performance. |
| Resource records | Read the resource-unit source and seven release-verification records. They record completed children, inactive leases and released probes. | These are historical records. This review did not inspect current process ownership or touch the shared lease. |

The copied image costs O(N*D) byte work for N passes and image size D, in addition to existing path work. It includes padding, inactive enum payload and unused capacity in nested fixed/limited fields. Copying these bytes is consistent with the full-image design, but can be much more work than reading only a used field. The code has no new per-pass guest heap allocation, data-stack reservation or callback. Memory growth can still occur when the activation frame is reserved.

A binder uses max(1,D) frame bytes. Frames sum distinct binders, including nested loops, inline clones, untaken branches and zero-trip loops. Repeated function activations can repeat growth/stack work; recursive active frames accumulate. The exclusive frame end is checked against memory32. Restoring a logical top does not shrink addressable Wasm pages or prove physical pages were released. Large global capacities also retain addressable space even when unused capacity is absent from the module's data bytes.

Compiler costs include one fixed-owner map entry per distinct nominal binder, slot entries, type/support/size/layout cache entries, and emitted scratch/code storage. The new branch adds nominal tests to the storage/binding/emission walks. `NoteType`, support checks and fixed-size checks have caches; first validation can still traverse the referenced type graph and field layouts. Existing unordered-map/vector/string allocations and their growth remain. There is no new compiler allocation that runs once per guest pass. There are five additional scratch locals for each emitted aggregate copy site: selected address, destination owner address, two copy addresses and copy length. Repeated defer emission can add more code and scratch for its multiple exit sites, while retaining one physical binder slot. No CPU or allocation profile establishes the size of these compiler costs.

[static-audit.json](static-audit.json) independently decodes the saved module sections and main instructions. It is an artifact inspection, not a Wasm validator. All 12 footprint modules have 13 main locals, one 8-byte frame reserve before the loop, no reserve inside it, and one `memory.copy 0 0`. O0 and O2 give the same values below.

| Source extent | Module bytes | Main function body bytes, including local declarations | Binder bytes |
| --- | ---: | ---: | ---: |
| Fixed length 0 | 1,111 | 213 | 8 |
| Fixed length 1 | 1,118 | 213 | 8 |
| Fixed length 32 | 1,358 | 213 | 8 |
| Fixed length 256 | 3,156 | 215 | 8 |
| Limited capacity 32, length 1 | 1,145 | 219 | 8 |
| Limited capacity 65,536, length 1 | 1,164 | 222 | 8 |

These sizes show bounded loop scratch for the tested shapes. They are absolute sizes, not a code-size gain over the parent. Literal initialization and encoding widths explain why whole module/body sizes can differ. The new syntax was rejected by the parent, so there is no direct parent module for it. No engine-native-code size was measured.

The queued handoff in `docs/wasm/measurements.md:110-132` is concrete and appropriate. It names the exact parent/candidate compiler identities, shared scalar/reference/constructor/match/callback/default controls, and a parent-accepted `for &e` plus explicit `copy(e)` comparison for the new syntax. It separates compiler, initialization and guest phases and includes pass count, path depth, image size, nested binders, reference memory, inactive payload, unused capacity, cold/warm calls, early exits, defer cleanup and growth boundaries. It calls for raw samples, identities, allocation/RSS data, code size, logical tops, addressable pages and separate physical-retention evidence. It also requires a new coordinated lease and host controls. Numeric noise/decision thresholds and the actual controlled host window still need to be set when that work starts. There is no basis here to claim a speed gain, a minimal measured memory footprint, or completed performance acceptance.

Coverage is sufficient for this narrow source-review conclusion, but not exhaustive. Dedicated large-image throughput, deeply nested path scaling, compiler allocation and other-platform execution remain unmeasured. The new fixtures do not isolate every integer index width or every const/optional/reference-type combination. The source keeps the shared paths and guards, and the accepted-parent comparisons support their stability; these omissions are not confirmed errors. A future wider change must add coverage for the wider paths.

The review inventory follows. Every review file was read in full, including unchanged portions of the three production headers and the test runner. Line ranges below describe content read, not just search matches. [file-inventory.json](file-inventory.json) also lists the exact unread ranges of every context file. Search hits outside the stated context ranges were used only for navigation.

| Review file | Inspected lines | Review focus |
| --- | --- | --- |
| `docs/wasm/evidence/fixed-aggregate-iteration.md` | 1-118 | Scope, results, corrections, cost claims and record limits. |
| `docs/wasm/measurements.md` | 1-132 | Prior results kept separate; iteration measurement handoff at 110-132. |
| `docs/wasm/status.md` | 1-265 | Increment status and retained target limits. |
| `src/wasm_arrays.h` | 1-743 | All array helpers; copy guard, path capture, current length, element address and cleanup order. |
| `src/wasm_codegen.h` | 1-1203 | All code; type guards, binding, callbacks, defaults, exits, activation and global initialization. |
| `src/wasm_storage.h` | 1-225 | All code; nominal copy plan, runtime-child discovery, frame sizes and data-stack accounting. |
| `test/expected/wasm_aggregate_iteration_callbacks.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_checkpoint.out` | 1-6 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_cleanup.out` | 1-6 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_control.out` | 1-2 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_defaults.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_enums.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_fields.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_identity.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_limited_empty.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_paths.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_refs_packed.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_refs_thin.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_values.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_walk_packed.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/expected/wasm_aggregate_iteration_zero_control.out` | 1-1 | Exact expected output checked with its fixture and saved streams. |
| `test/wasm/wasm_aggregate_iteration_callbacks.goose` | 1-7 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_checkpoint.goose` | 1-11 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_cleanup.goose` | 1-17 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_control.goose` | 1-11 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_defaults.goose` | 1-6 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_enums.goose` | 1-12 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_fields.goose` | 1-15 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_identity.goose` | 1-9 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_limited_empty.goose` | 1-14 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_paths.goose` | 1-15 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_refs_packed.goose` | 1-8 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_refs_thin.goose` | 1-8 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_values.goose` | 1-13 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_walk_packed.goose` | 1-10 | Fixture behavior and expected output checked together. |
| `test/wasm/wasm_aggregate_iteration_zero_control.goose` | 1-6 | Fixture behavior and expected output checked together. |
| `test/wasm_aggregate_admission.py` | 1-118 | Native-first exclusions and compile-only range limits; removed iteration rejection. |
| `test/wasm_backend.py` | 1-596 | Full runner; fixture inclusion, owner checks, new controls, limits and footprint calls. |
| `test/wasm_iteration_checks.py` | 1-143 | Specific damaged-module failures, validation, binder limit and static footprint. |
| `test/wasm_iteration_owner.mjs` | 1-50 | Live completion, neighbor sentinel, zero-trip binder, outer owner and inner top. |

| Context file | Inspected lines | Unread lines |
| --- | --- | --- |
| `src/wasm_fixed.h` | 1-465 | None |
| `src/wasm_support.h` | 1-97 | None |
| `test/wasm_aggregate_checks.py` | 1-119 | None |
| `src/clone.h` | 245-270, 550-610 | 1-244, 271-549, 611-740 |
| `src/optimize.h` | 660-716, 1040-1080, 1480-1505 | 1-659, 717-1039, 1081-1479, 1506-1531 |
| `src/typecheck_exprs.h` | 1-110, 490-555 | 111-489, 556-3427 |
| `src/typecheck_types.h` | 730-785 | 1-729, 786-1751 |
| `src/codegen_construct.h` | 1-70, 900-970 | 71-899, 971-1407 |
| `src/value_layout.h` | 1-399 | None |
| `src/wasm_memory.h` | 1-228 | None |
| `src/wasm_binary.h` | 1-191 | None |
| `src/data_stacks.h` | 1-79 | None |
| `src/ast.h` | 1310-1370, 1680-1730 | 1-1309, 1371-1679, 1731-2967 |
| `src/codegen_nodes.h` | 975-1235 | 1-974, 1236-1297 |
| `src/codegen_values.h` | 475-530 | 1-474, 531-2060 |
| `src/codegen_stmts.h` | 650-735 | 1-649, 736-1215 |
| `src/typecheck_flow.h` | 1944-2145 | 1-1943, 2146-3242 |
| `scripts/run_wasm.mjs` | 1-149 | None |
| `test/wasmtime_host.py` | 1-169 | None |
| `test/wasm_multimemory.mjs` | 1-85 | None |
| `test/backend_shared.py` | 1-71 | None |
| `test/run_tests.py` | 1-55, 1365-1490 | 56-1364, 1491-2882 |
| `CMakeLists.txt` | 1-150 | 151-236 |

Evidence content inspection included the native/build/control harness sources, frozen-source verifier, compatibility scripts, source/test/module manifests, targeted command/status records and streams, original/corrected enum source, original/corrected adapter identities, control and zero-control saved main WAT, full-suite summary streams, native baseline ending/skip sections, static footprint data and the resource-unit/release records. The 12 static modules were decoded for the stated counts and instructions. All other inventoried raw artifacts were hashed; they were not all disassembled or read line by line. In particular, most generated native C, native executable internals, most module instructions, and unrelated older evidence documents were not substantively reviewed. The prior scalar timing studies cited by the documents were not re-audited for this increment.

No requested source snapshot or listed raw artifact was unavailable. The missing original build-unit native manifest and missing full-suite per-command streams are the record limits described above. The later log-name proposal was not executed and is not treated as evidence. Final identity results are saved in `identity-after.json`.
