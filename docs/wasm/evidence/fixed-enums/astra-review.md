**Assessment**

No confirmed production defect was found in the frozen fixed-enum increment. The reviewed design is consistent with the stated limited scope. The saved functional results support this assessment. Performance acceptance remains open: no new compiler timing, allocation, guest throughput, or physical-memory measurements exist.

This was an independent, read-only review on 2026-11-07. I did the review myself. I did not use child agents or Claude. I did not run builds, tests, validators, guest runtimes, debuggers, or timing jobs. I used file reads, Git reads, hashes, and analysis of saved files. The only file written by this review is this report. No PR exists and no commit or push was made.

**Frozen identity and hash results**

- Worktree: `/home/dev/Projects/goose-wasm-backend`.
- Branch: `feat/wasm-multimemory-backend`.
- Baseline and current HEAD: `268b37b1a4203e8ebceb0f1c0e51321c3be91b4f`.
- Candidate: the staged diff, not a new commit.
- Saved and live staged patch SHA-256, before and after review: `de9ee154e9b9b08a7edc4cb05c67976f5f02ed429004ba092aa16d63b6d144a6`.
- All 356 paths in `scope.json.hashes` matched both the worktree bytes and the Git index bytes before and after review. The set of staged paths equals this manifest exactly.
- All 68 snapshot hashes matched before and after review. These include all 53 review files and 15 context files.
- Repaired compiler SHA-256: `250902481fe28fadfd7102f7ac64475814c864dbc91ff2060ce5b9ed360eb73c`.
- First enum compiler SHA-256: `673d4b3efb9277d94441e5a79b57f8cf8e730dc165e382581a699d5426526f51`.
- Accepted struct compiler SHA-256: `7fdb4c2236fcfddb599c0426e23ba5547779ec0ef0f27790545a886b4edd1d54`.
- All C++ source entries and `CMakeLists.txt` in the repaired compiler's 103-entry source manifest match. Its only current manifest difference is `test/wasm_backend.py`, which was extended after that build. The full-suite manifest matches the current test source. Its only current difference is generated `test/__pycache__/wasm_backend.cpython-313.pyc`. This review did not import that module or write bytecode.
- All 1,309 entries in `artifact-hashes.json` match their recorded size and hash. All 160 entries in `final-modules.json` match their size, hash, and independently decoded local counts.
- The derived `pre-repair-wasm_codegen.h` hash is `0df3921105b8c490a7ea14fa148782dfd4227e4c355992c37f44a5875c9ce43a`. It matches the original build01 source manifest. It is a reconstruction, not an original backup.

The initial and final checks had zero staged-file or snapshot mismatches. Hash checks establish identity, not correctness or reproducible builds. I did not rebuild the compiler.

**Confirmed findings**

None. I found no valid, in-scope triggering case that establishes a wrong result, unsafe write, invalid module, ownership error, or guard bypass in this candidate. Thus there is no defect severity or proposed production fix in this report. The risks and test gaps below are not confirmed defects.

**Correctness and design assessment**

1. **Shared layout bounds.** `src/value_layout.h:265` adds bounded field layout calculation. Child sizes are checked before `LayoutFields` uses them. Additions and array products are bounded before use. Enum sizes include the tag plus the largest payload. The tag uses u8 through 256 variants and u16 above that; empty or more than 65,536 variants are rejected. Cached fixed sizes are checked against each requested limit. Layout entries are installed only after their own field layout fits. Failure can leave valid child layouts cached, but does not mark a failed root as admitted.
2. **Selected variants and reference graphs.** `src/wasm_support.h:65` checks every payload for a whole enum. Its standalone variant branch checks only the selected payload. Thus `Mixed.Fixed` can be used when another variant is nonfixed. Reference graph admission uses a seen set and publishes success only after the graph passes. Relative/pool references, root structs, nonfixed fields, and aggregate array elements remain guarded. The Hidden and Mixed fixtures exercise the distinction between a fixed stored reference and a nonfixed owner.
3. **Fresh storage and zero sizes.** `src/wasm_storage.h:15` records owner image size and storage size separately. `src/wasm_fixed.h:38` checks the owner and its initialization node. `FixedChild` checks the child range with subtraction before adding offsets. Empty standalone variants have a zero-byte image and one byte of owner storage. Empty enum payloads add no identity byte. The explicit root-only empty write does not become a nested payload write. Pad-only layouts retain their declared image size.
4. **Construction and evaluation order.** `src/wasm_fixed.h:248` consumes the checked initializer order and builds each field before the next field's effects. Defaults use checked `defaultinit`. Exact copies use the actual stored source type and reject layout adaptation. Fixed arrays use bounded storage; fills capture their value once, including zero-count fills. Literal constructor scratch is reused for limited fields. No general aggregate value ABI is inferred from an address.
5. **Fields and references.** `src/wasm_fixed.h:194` resolves the receiver place before looking up its field type and offset. It does not rely on a missing syntactic struct instance. Calls, inlined reference returns, nested fields, and indexed reference elements use the stored receiver layout. Optional dereferences check null. Packed offsets use checked low-address addition where required. Assignment captures its field address before right-hand effects. The ordinary reference representation follows the complete storage scan, including hidden enum field references.
6. **Statement matches.** `src/wasm_fixed.h:372` resolves the source once, loads the tag once, and checks the unsigned tag range before dispatch. A wildcard does not bypass this check. Each selected binder gets its own planned Memory 0 owner. The copy length is the selected variant image, not the maximum enum payload or a borrowed interior reference. Empty payloads do not cause a payload read. The binder copy occurs before arm effects. The checker requires fixed-mode binders to be copies and rejects fixed-mode reference binding in `src/typecheck_flow.h:1501` onward.
7. **Cleanup and storage interactions.** Match arms add a cleanup scope and use the existing statement and exit paths. Normal arm completion, return, break, continue, and defer retain their scope behavior. Frame slots live for the function activation. Data-stack planning resets the arm's incoming logical stack position for each mutually exclusive arm. Deferred work remains above live owners. Existing completion checks observe frame and data tops after `_start` returns; they do not infer completion from sleeps or old addresses.
8. **Checked callbacks.** `src/wasm_codegen.h:346` and `:357` now use `RunChildren`. That walk includes checked callback bodies and checked default initializers. This agrees with emission and with `src/clone.h:596`. Callback parameters still get scalar/reference ABI checks. Match binders in checked callback bodies get both a storage plan and a slot. No new closure ABI is introduced.
9. **Copy dispatch.** `src/wasm_arrays.h:100` selects the new helper only for a known Memory 0 destination with a dynamic source. `src/wasm_memory.h:149` dispatches once on the source high word, wraps the source offset, and uses a fixed source memory in `memory.copy`. Invalid identities reach the existing failure path. Both-known copies stay direct. Both-dynamic copies retain the general helper. The destination is already proven to be in Memory 0 before its i64 address is wrapped.
10. **Guarded features and module structure.** Calls and inlined argument bindings reject by-value aggregates. Whole assignments, operators, printing, value matches, adaptation, and aggregate elements retain explicit guards. The new host failure code uses the existing import. Shared layout additions have no new platform-specific branch or native runtime dependency. The shared bounded-query changes are used by Wasm admission; native layout emission is unchanged. Linux native and exact-output evidence supports that limited conclusion. It does not establish Windows, macOS, or another CPU's native behavior.

**Tests and saved failure evidence**

All 16 new Goose fixtures and all 16 expected-output files were read. The fixtures check packed fields, padding, tag widths, defaults, exact copies, nested enum/variant fields, empty identity, references in arrays, callbacks, side effects, and cleanup. The new admission cases emit, compile, and run native C before checking the Wasm rejection. Large layout cases are compile-only checks and do not request their declared storage.

The enum mutation controls in `test/wasm_enum_checks.py` validate the modified module, then require the intended runtime error, the exact source line, and no stdout. The wrong payload offset targets `p.x`; the shortened copy targets `p.z`; the widened field read targets `p.y`; invalid tags target the match line, including a wildcard; the shortened u16 tag store reaches the designated wildcard assertion. These controls discriminate the intended failures. They are not merely counts of rejected modules. The direct helper tests cover all 65 source identities, invalid identities, zero-length boundary copies, overlap, and no-write behavior on out-of-bounds copies under both engines.

The saved diagnosis is valid failing-first evidence for the callback repair:

- Scalar local and scalar address callbacks fail with `out-of-line captured locals are not implemented` at O0 and O2 in both the accepted struct compiler and build01. Their native runs return 8 and 9.
- The struct inline callback fails at O2 with that error in both old compilers. O0 passes and is a control, not a reproduced failure. Its native output is 11.
- The enum callback match fails in build01 at O0 and O2 with that error. The prior struct compiler rejects the enum at its earlier unsupported-layout guard; that is not evidence of the same bug. Its native output is 8.
- The default callback passes in the old forms and is a coverage control. Its native output is 3.
- `diagnosis01` has aggregate exit 1 because its broad expectation wrongly required the passing controls to fail. All 50 per-command recorded exit codes agree with the raw exit files.
- All 112 build02 repair command records have exit 0. The harness compares Node and Wasmtime stdout with the expected bytes and requires empty stderr. The current full suite also contains the repair fixtures and the original combined enum-reference fixture.

The native01 reserved-name failure and remaining01 invalid temporary match are frontend-invalid inputs. They are not production Wasm defects. The remaining01 variable enum reached a valid nonfixed-variant guard rather than the expected parent-enum wording. The corrected native02 empty fixture passes. No failed attempt was counted as a successful final run.

The archived final functional result is `wasm backend: 744 checks passed`, with Node 24.22.2, wasm-tools 1.262.0, and Wasmtime Python 49.0.0. This is a mixture of controls and executions, not 744 independent programs. The full native baseline log says all tests passed with four workers and an explicit TinyCC path. It preserves device/platform/JIT skips. These are saved results, not jobs run during this review.

**Independent module and compatibility assessment**

All 52 saved exact comparison pairs were compared again as files: output bytes, stdout, stderr, and exit records match. That exact-comparison reference is the older inline checkpoint with hash `63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`, as recorded in its summary. It is not the accepted struct compiler. The separate prior-module comparison does use the accepted struct compiler.

All 136 prior-module binary pairs, their saved hashes, sizes, and diagnostic files were checked. There are 130 equal pairs and six changed pairs. I independently split the saved before/after WAT into top-level forms and compared all non-helper content after removing numeric function/type annotations. I did not execute the supplied classification script. The only changed call instructions wrap the known-zero destination to i32 and call `goose.copy_to_frame`. The only removed signature is the unused `(i64, i64, i32) -> ()` generic copy signature. Other function instructions, imports, memories, globals, exports, and data match under this index normalization.

| Pair | Bytes before | Bytes after | Changed calls |
| --- | ---: | ---: | ---: |
| struct cleanup O0 | 3307 | 3201 | 1 |
| struct cleanup O2 | 4063 | 3958 | 2 |
| struct references O0 | 15858 | 14583 | 1 |
| struct references O2 | 15858 | 14583 | 1 |
| struct packed calls O0 | 4150 | 4044 | 1 |
| struct packed calls O2 | 4095 | 3989 | 1 |

The cleanup and packed-call helper changes replace four memory-pair cases with two source cases. The reference helper changes replace 64 pair cases with eight source cases. I inspected the new case bodies, branch targets, selected memory operands, and invalid-identity tail. This supports the supplied helper-only classification. It does not establish a runtime speed gain.

**Footprint, work, and cost**

The cheapest clear design for this limited scope is the present separate owner plus selected-image copy. It avoids an interior reference with invalid lifetime or mutation semantics. I found no reason to replace it with a general destination or aggregate ABI as part of this increment.

Static sizes were decoded independently from the retained binaries, without loading or running them:

| Saved case | Static result |
| --- | --- |
| Copy-to-frame helper, 3 memories | 79-byte function body |
| Generic copy helper, 3 memories | 286-byte function body |
| Copy-to-frame helper, 65 memories | 1133-byte function body |
| Generic copy helper, 65 memories | 78158-byte function body |
| Enum limited-field literal, 32 elements, O0/O2 | 28 main locals; 10343-byte module; 4015-byte main body |
| Enum limited-field literal, 256 elements, O0/O2 | 28 main locals; 73972-byte module; 29937-byte main body |

Function-body sizes include local declarations and the final end opcode. The helper has no locals. Constant local count does not mean constant code size or compiler memory use. The 224 extra literal elements add 63,629 module bytes. The emitter still emits each element's expression, checks, and stores; diagnostic data also contributes to the module. Fill constructors use a loop and one captured item instead.

The runtime match work is one source evaluation, one tag load and range check, comparisons through the selected arm, and one selected-payload copy when a binder exists. A multi-variant arm emits all its equality tests. Exact enum owner copies use the whole fixed image. Copy cost therefore grows with bytes copied. This is required by the stored-value copy design; it adds no explicit guest heap allocation beyond the planned frame and possible frame growth. Dynamic source copies use one memory dispatch instead of two nested dispatches. Engine code generation and throughput gains are unmeasured.

Compiler work includes the owner map entry per nominal declaration or binder, field-layout vectors, support worklists and sets, fixed-size cache entries, emitted instruction/data buffers, and checked AST walks. `Scan` and `BindTree` visit checked callback/default bodies. `FixedChild` and field lookup repeat admission/size lookups, usually cache hits. `TryFieldLayout` still calls `LayoutFields`, whose `FixedSize` can traverse enum variants again; `Cls` also traverses standalone variant fields. Do not assume every nested/repeated type query is constant time. There are no allocation samples to quantify these costs.

Frame storage sums all bound fixed owners, including mutually exclusive match binders. For payload sizes s1 through sn, their binder contribution is the sum of max(1, si), not the largest si. Recursion multiplies active frame demand. Memory growth restores the logical top but retains pages. Globals reserve zero-filled static ranges without serializing unused capacity. These facts support logical footprint statements only, not low physical RSS or a minimal retained footprint.

The new helper is lazy and shared per module. The general helper remains available and quadratic in memory count when both identities are dynamic. Prior scalar and array callers are constrained by the 130 byte-identical pairs; six struct pairs benefit in module size. No measured regression was found because no new performance measurements were supplied. A lack of samples is not a measured pass.

**Unverified risks and suggested follow-up**

- **Frame growth under many arms.** `src/wasm_codegen.h:328` and `:361` reserve separate binder slots. A large fixed enum with many bound arms can need much more frame space than the active payload. This is an explicit design cost, not a confirmed ownership defect. Measure maximum live frame bytes and retained pages before adding slot reuse. Any reuse must preserve defer and escaped-reference rules.
- **Compiler cost for deep/repeated layouts.** `src/value_layout.h:265` and `:358`, plus `src/wasm_fixed.h:6` and `:54`, can repeat layout and field-path work. Include deep fields, repeated variant types, and zero-sized nested variants in a compile-only cost study. No explosive case or measured regression was established in this review. Do not add broader caching without first showing the hot query and its cost.
- **Coverage for unequal nonempty payloads.** The current short-copy control uses one nonempty payload and an empty alternative. A useful further discriminating test has a small selected payload, a much larger unselected payload, and adjacent live data after the binder. A derived control that copies the maximum enum payload must fail at a specific neighboring-data assertion. The implementation already selects the right size; this is a test-strength limit.
- **Widened callback/default paths.** Existing scalar, struct, inline-reference, and enum callback fixtures pass in saved evidence. Add a callback/default case that also owns data arrays, calls at multiple stack bases, and exits through defer if this path is widened again. No current failing case is established.

**Measurement and coverage limits**

Compiler CPU, RSS, allocation counts, guest throughput, engine native-code size, and physical retained memory remain unmeasured for this increment. No cross-architecture native result is supplied. Cross-compilation or emulation would not substitute for native runtime evidence. Old scalar timing windows are closed and their samples do not establish this increment's cost.

The task names `report/measurements.md`, but that file was not found under the review packet, raw evidence root, archived evidence root, or the worktree's `report` directory. The worktree has no such `report` directory. The available handoff is in `docs/wasm/measurements.md` and `docs/wasm/evidence/fixed-enums.md`. It names the two compiler identities and the required scalar, callback, field-path, literal/fill, match, thin/packed-copy, and 3/65-memory cases. It requires separate compile/init/run phases, host controls, allocation/retention evidence, and a fresh coordinated lease. This is a concrete queued measurement plan, not a timing grant or completed result.

All 53 requested review files were inspected. No review file is unread. Context files were inspected only to the extent listed below; this is not a full audit of the typechecker, native backend, or test runner. All archived evidence files were hashed, but not all were read as text or disassembled. In particular, most generated C runtime prefixes, native executable internals, unchanged prior-module instruction streams, and raw passing stdout/stderr files were not individually inspected. Hash equality and harness checks are not a claim of semantic review of every retained artifact. Full-suite subprocess output is captured by the harness; the saved suite pass log is relied on for execution results of its final mutation controls. No new failure was reproduced during this review because execution was prohibited.

**Evidence inventory**

The archived evidence root is `/home/dev/Projects/goose-wasm-backend/docs/wasm/evidence/fixed-enums`. The raw root is `/tmp/goose-wasm-fixed-enum-20261107`.

| Unit or manifest | Inspection and result |
| --- | --- |
| build01 | Build identity/source manifest, preserved compiler hash, first failure diagnostic, summary and 80 per-command exit records. Initial unit exit 1 remains preserved. |
| diagnosis01 | Harness, five fixture sources, native outputs, old/prior diagnostics, selected generated native function bodies, summary and all 50 per-command exit records. |
| build02 | Harness, compiler/source identity, build stderr, summary and all 112 per-command exit records. All command exits are zero. |
| native01/native02 | Native fixture hashes, summaries, reserved-name diagnostics, corrected result, and all 66/8 per-command exit records. |
| remaining01 | All 143 per-command exit records, summary, admission diagnostics and native-invalid temporary diagnostic. Exit 1 is explained above. |
| full-wasm01 | Commands, source/test identity manifests, exit and pass log, retained modules, constructor sizes, and current harness/control source. |
| native-baseline01 | Command and complete baseline stdout, exit, source identity and recorded skips. |
| compatibility01 | Exact comparison harness and 52 raw output/diagnostic/exit pairs; all 136 prior binary pairs, hashes, sizes, diagnostics and exits. |
| module-audit01 | All six before/after WAT pairs processed independently, classification and supplied verification source read, 12 print exit records checked. Saved diff files hashed. |
| artifact-hashes.json | All 1309 retained artifact sizes and hashes checked. |
| final-modules.json | All 160 retained module sizes, hashes and local-count lists checked. |
| constructor/copy-helper footprint | Read and independently checked from saved binary section bytes. |
| reconstruction.json | Method and reconstructed file hash checked against build01's original source manifest. |
| leases/releases | All ten unit records state owner exited, children reaped, inactive lease, no owned processes, successful nonblocking probe, and released probe. These are saved records; I did not probe the current host lease. |

**Review files inspected**

Every path below was read for this review and passed both initial and final worktree/index/snapshot checks.

- `docs/wasm/evidence/fixed-enums.md`
- `docs/wasm/measurements.md`
- `docs/wasm/status.md`
- `scripts/run_wasm.mjs`
- `src/value_layout.h`
- `src/wasm_arrays.h`
- `src/wasm_codegen.h`
- `src/wasm_fixed.h`
- `src/wasm_memory.h`
- `src/wasm_storage.h`
- `src/wasm_support.h`
- `test/expected/wasm_callback_address.out`
- `test/expected/wasm_callback_default.out`
- `test/expected/wasm_callback_inline_reference.out`
- `test/expected/wasm_callback_local.out`
- `test/expected/wasm_enum_callback_match.out`
- `test/expected/wasm_enum_cleanup.out`
- `test/expected/wasm_enum_containers.out`
- `test/expected/wasm_enum_control.out`
- `test/expected/wasm_enum_effects.out`
- `test/expected/wasm_enum_empty.out`
- `test/expected/wasm_enum_hidden.out`
- `test/expected/wasm_enum_layout.out`
- `test/expected/wasm_enum_references.out`
- `test/expected/wasm_enum_tags.out`
- `test/expected/wasm_enum_variant.out`
- `test/expected/wasm_enum_wildcard.out`
- `test/wasm/wasm_callback_address.goose`
- `test/wasm/wasm_callback_default.goose`
- `test/wasm/wasm_callback_inline_reference.goose`
- `test/wasm/wasm_callback_local.goose`
- `test/wasm/wasm_enum_callback_match.goose`
- `test/wasm/wasm_enum_cleanup.goose`
- `test/wasm/wasm_enum_containers.goose`
- `test/wasm/wasm_enum_control.goose`
- `test/wasm/wasm_enum_effects.goose`
- `test/wasm/wasm_enum_empty.goose`
- `test/wasm/wasm_enum_hidden.goose`
- `test/wasm/wasm_enum_layout.goose`
- `test/wasm/wasm_enum_references.goose`
- `test/wasm/wasm_enum_tags.goose`
- `test/wasm/wasm_enum_variant.goose`
- `test/wasm/wasm_enum_wildcard.goose`
- `test/wasm_backend.py`
- `test/wasm_copy_matrix.mjs`
- `test/wasm_copy_matrix.py`
- `test/wasm_enum_admission.py`
- `test/wasm_enum_checks.py`
- `test/wasm_fixed_layout.cpp`
- `test/wasm_memory.cpp`
- `test/wasm_memory.mjs`
- `test/wasm_memory.py`
- `test/wasmtime_host.py`

**Context inspection**

- `src/ast.h`: Selected MatchArm, MatchExpr, StructLit, enum instance, field-run, and VariantIndex definitions.
- `src/clone.h`: Checked RunChildren and match/inline/block child enumeration.
- `src/typecheck_flow.h`: CheckMatch, enum pattern and copy/reference binder rules; statement-match entry points.
- `src/codegen_nodes.h`: Native MatchExpr::CgAny and related literal/match entry points.
- `src/codegen_stmts.h`: Search of checked-tree walkers and binder treatment; not read in full.
- `src/codegen_values.h`: Search of variant field/value lowering and stored-location entry points; not read in full.
- `src/wasm_binary.h`: Full encoder, data reservations, memory limits and function/name sections.
- `src/data_stacks.h`: Full shared call-bound and recursive-component accounting.
- `src/main.cpp`: Backend and shared-header inclusion order; not a full driver review.
- `CMakeLists.txt`: Compiler language setting and target source/header list; remaining build logic not reviewed.
- `test/backend_shared.py`: Full exact comparison harness.
- `test/run_tests.py`: Baseline/worker/skip entry points searched; full runner not reviewed.
- `test/wasm_multimemory.mjs`: Full completion and owner-state harness.
- `test/wasm_struct_checks.py`: Full mutation controls and constructor-local checks.
- `test/wasm_struct_admission.py`: Full shared struct admission and overflow cases.

Selected generated native function bodies in diagnosis01 were also read. Their shared runtime prefixes were not fully reviewed. Additional raw harnesses read: diagnosis01/checks.py, build02/checks.py, and compatibility01/prior-modules.py.

**Archived evidence file list and hash coverage**

Each file below passed the initial and final staged/worktree hash check against `scope.json`. This is the complete archived evidence file inventory. Text review is at the unit/manifest depth stated above. Files outside that stated depth were hash-only inputs; their content is an explicit unread-evidence limit.

- `artifact-hashes.json`
- `build01/build-identity.json`
- `build01/checks.py`
- `build01/commands.json`
- `build01/enum-checks.exit`
- `build01/enum-checks.stderr`
- `build01/enum-checks.stdout`
- `build01/freeze.exit`
- `build01/freeze.py`
- `build01/freeze.stderr`
- `build01/freeze.stdout`
- `build01/lease.json`
- `build01/memory-build.exit`
- `build01/references-O2-emit.exit`
- `build01/references-O2-emit.stderr`
- `build01/release-build.exit`
- `build01/release-build.stderr`
- `build01/release-build.stdout`
- `build01/release-verification.json`
- `build01/results.json`
- `build01/source-hashes.json`
- `build01/summary.json`
- `build01/unit.exit`
- `build01/unit.stderr`
- `build01/unit.stdout`
- `build02/build-identity.json`
- `build02/checks.py`
- `build02/commands.json`
- `build02/freeze.exit`
- `build02/freeze.py`
- `build02/freeze.stderr`
- `build02/freeze.stdout`
- `build02/lease.json`
- `build02/release-build.exit`
- `build02/release-build.stderr`
- `build02/release-build.stdout`
- `build02/release-verification.json`
- `build02/repair-checks.exit`
- `build02/repair-checks.stderr`
- `build02/repair-checks.stdout`
- `build02/results.json`
- `build02/source-hashes.json`
- `build02/summary.json`
- `build02/unit.exit`
- `build02/unit.stderr`
- `build02/unit.stdout`
- `compatibility01/commands.json`
- `compatibility01/exact-comparisons.exit`
- `compatibility01/exact-comparisons.stderr`
- `compatibility01/exact-comparisons.stdout`
- `compatibility01/exact/summary.json`
- `compatibility01/lease.json`
- `compatibility01/prior-module-summary.json`
- `compatibility01/prior-modules.exit`
- `compatibility01/prior-modules.py`
- `compatibility01/prior-modules.stderr`
- `compatibility01/prior-modules.stdout`
- `compatibility01/release-verification.json`
- `compatibility01/source-identity.exit`
- `compatibility01/source-identity.stderr`
- `compatibility01/source-identity.stdout`
- `compatibility01/unit.exit`
- `compatibility01/unit.stderr`
- `compatibility01/unit.stdout`
- `compatibility01/wasm_frames-O0-after.exit`
- `compatibility01/wasm_frames-O0-before.exit`
- `compatibility01/wasm_frames-O2-after.exit`
- `compatibility01/wasm_frames-O2-before.exit`
- `compatibility01/wasm_struct_review_fields_packed-O0-after.exit`
- `compatibility01/wasm_struct_review_fields_packed-O0-before.exit`
- `compatibility01/wasm_struct_review_fields_packed-O2-after.exit`
- `compatibility01/wasm_struct_review_fields_packed-O2-before.exit`
- `compatibility01/wasm_struct_review_fields_thin-O0-after.exit`
- `compatibility01/wasm_struct_review_fields_thin-O0-before.exit`
- `compatibility01/wasm_struct_review_fields_thin-O2-after.exit`
- `compatibility01/wasm_struct_review_fields_thin-O2-before.exit`
- `compatibility01/wasm_tail_values-O0-after.exit`
- `compatibility01/wasm_tail_values-O0-before.exit`
- `compatibility01/wasm_tail_values-O2-after.exit`
- `compatibility01/wasm_tail_values-O2-before.exit`
- `constructor-footprint.json`
- `copy-helper-footprint.json`
- `diagnosis01/checks.py`
- `diagnosis01/commands.json`
- `diagnosis01/default-callback-O0-before.stderr`
- `diagnosis01/default-callback-O0-native-run.stdout`
- `diagnosis01/default-callback-O0-prior.stderr`
- `diagnosis01/default-callback-O2-before.stderr`
- `diagnosis01/default-callback-O2-native-run.stdout`
- `diagnosis01/default-callback-O2-prior.stderr`
- `diagnosis01/default-callback.goose`
- `diagnosis01/enum-callback-match-O0-before.exit`
- `diagnosis01/enum-callback-match-O0-before.stderr`
- `diagnosis01/enum-callback-match-O0-native-run.stdout`
- `diagnosis01/enum-callback-match-O0-prior.exit`
- `diagnosis01/enum-callback-match-O0-prior.stderr`
- `diagnosis01/enum-callback-match-O2-before.exit`
- `diagnosis01/enum-callback-match-O2-before.stderr`
- `diagnosis01/enum-callback-match-O2-native-run.stdout`
- `diagnosis01/enum-callback-match-O2-prior.exit`
- `diagnosis01/enum-callback-match-O2-prior.stderr`
- `diagnosis01/enum-callback-match.goose`
- `diagnosis01/failing-first.exit`
- `diagnosis01/failing-first.stderr`
- `diagnosis01/failing-first.stdout`
- `diagnosis01/lease.json`
- `diagnosis01/release-verification.json`
- `diagnosis01/results.json`
- `diagnosis01/scalar-address-O0-before.exit`
- `diagnosis01/scalar-address-O0-before.stderr`
- `diagnosis01/scalar-address-O0-native-run.stdout`
- `diagnosis01/scalar-address-O0-prior.exit`
- `diagnosis01/scalar-address-O0-prior.stderr`
- `diagnosis01/scalar-address-O2-before.exit`
- `diagnosis01/scalar-address-O2-before.stderr`
- `diagnosis01/scalar-address-O2-native-run.stdout`
- `diagnosis01/scalar-address-O2-prior.exit`
- `diagnosis01/scalar-address-O2-prior.stderr`
- `diagnosis01/scalar-address.goose`
- `diagnosis01/scalar-local-O0-before.exit`
- `diagnosis01/scalar-local-O0-before.stderr`
- `diagnosis01/scalar-local-O0-native-run.stdout`
- `diagnosis01/scalar-local-O0-prior.exit`
- `diagnosis01/scalar-local-O0-prior.stderr`
- `diagnosis01/scalar-local-O2-before.exit`
- `diagnosis01/scalar-local-O2-before.stderr`
- `diagnosis01/scalar-local-O2-native-run.stdout`
- `diagnosis01/scalar-local-O2-prior.exit`
- `diagnosis01/scalar-local-O2-prior.stderr`
- `diagnosis01/scalar-local.goose`
- `diagnosis01/struct-inline-callback-O0-before.stderr`
- `diagnosis01/struct-inline-callback-O0-native-run.stdout`
- `diagnosis01/struct-inline-callback-O0-prior.stderr`
- `diagnosis01/struct-inline-callback-O2-before.exit`
- `diagnosis01/struct-inline-callback-O2-before.stderr`
- `diagnosis01/struct-inline-callback-O2-native-run.stdout`
- `diagnosis01/struct-inline-callback-O2-prior.exit`
- `diagnosis01/struct-inline-callback-O2-prior.stderr`
- `diagnosis01/struct-inline-callback.goose`
- `diagnosis01/summary.json`
- `diagnosis01/unit.exit`
- `diagnosis01/unit.stderr`
- `diagnosis01/unit.stdout`
- `final-modules.json`
- `full-wasm01/commands.json`
- `full-wasm01/full-wasm.exit`
- `full-wasm01/full-wasm.stderr`
- `full-wasm01/full-wasm.stdout`
- `full-wasm01/lease.json`
- `full-wasm01/release-verification.json`
- `full-wasm01/source-identity.exit`
- `full-wasm01/source-identity.stderr`
- `full-wasm01/source-identity.stdout`
- `full-wasm01/test-hashes.json`
- `full-wasm01/unit.exit`
- `full-wasm01/unit.stderr`
- `full-wasm01/unit.stdout`
- `full-wasm01/verify-source.py`
- `module-audit01/classification.json`
- `module-audit01/commands.json`
- `module-audit01/lease.json`
- `module-audit01/module-dumps.exit`
- `module-audit01/module-dumps.stderr`
- `module-audit01/module-dumps.stdout`
- `module-audit01/print.py`
- `module-audit01/release-verification.json`
- `module-audit01/results.json`
- `module-audit01/unit.exit`
- `module-audit01/unit.stderr`
- `module-audit01/unit.stdout`
- `module-audit01/verify-classification.py`
- `module-audit01/wasm_struct_cleanup-O0-after.stdout`
- `module-audit01/wasm_struct_cleanup-O0-before.stdout`
- `module-audit01/wasm_struct_cleanup-O0.diff`
- `module-audit01/wasm_struct_cleanup-O2-after.stdout`
- `module-audit01/wasm_struct_cleanup-O2-before.stdout`
- `module-audit01/wasm_struct_cleanup-O2.diff`
- `module-audit01/wasm_struct_refs-O0-after.stdout`
- `module-audit01/wasm_struct_refs-O0-before.stdout`
- `module-audit01/wasm_struct_refs-O0.diff`
- `module-audit01/wasm_struct_refs-O2-after.stdout`
- `module-audit01/wasm_struct_refs-O2-before.stdout`
- `module-audit01/wasm_struct_refs-O2.diff`
- `module-audit01/wasm_struct_review_calls_packed-O0-after.stdout`
- `module-audit01/wasm_struct_review_calls_packed-O0-before.stdout`
- `module-audit01/wasm_struct_review_calls_packed-O0.diff`
- `module-audit01/wasm_struct_review_calls_packed-O2-after.stdout`
- `module-audit01/wasm_struct_review_calls_packed-O2-before.stdout`
- `module-audit01/wasm_struct_review_calls_packed-O2.diff`
- `native-baseline01/commands.json`
- `native-baseline01/lease.json`
- `native-baseline01/native-baseline.exit`
- `native-baseline01/native-baseline.stderr`
- `native-baseline01/native-baseline.stdout`
- `native-baseline01/release-verification.json`
- `native-baseline01/source-identity.exit`
- `native-baseline01/source-identity.stderr`
- `native-baseline01/source-identity.stdout`
- `native-baseline01/unit.exit`
- `native-baseline01/unit.stderr`
- `native-baseline01/unit.stdout`
- `native01/cleanup-O0-native-run.stdout`
- `native01/cleanup-O0-prior-wasm.exit`
- `native01/cleanup-O2-native-run.stdout`
- `native01/cleanup-O2-prior-wasm.exit`
- `native01/commands.json`
- `native01/containers-O0-native-run.stdout`
- `native01/containers-O0-prior-wasm.exit`
- `native01/containers-O2-native-run.stdout`
- `native01/containers-O2-prior-wasm.exit`
- `native01/effects-O0-native-run.stdout`
- `native01/effects-O0-prior-wasm.exit`
- `native01/effects-O2-native-run.stdout`
- `native01/effects-O2-prior-wasm.exit`
- `native01/empty-O0-native-emit.exit`
- `native01/empty-O0-native-emit.stderr`
- `native01/empty-O2-native-emit.exit`
- `native01/empty-O2-native-emit.stderr`
- `native01/empty.goose`
- `native01/golden.py`
- `native01/hidden-O0-native-run.stdout`
- `native01/hidden-O0-prior-wasm.exit`
- `native01/hidden-O2-native-run.stdout`
- `native01/hidden-O2-prior-wasm.exit`
- `native01/layout-O0-native-run.stdout`
- `native01/layout-O0-prior-wasm.exit`
- `native01/layout-O2-native-run.stdout`
- `native01/layout-O2-prior-wasm.exit`
- `native01/lease.json`
- `native01/native-oracles.exit`
- `native01/native-oracles.stderr`
- `native01/native-oracles.stdout`
- `native01/references-O0-native-run.stdout`
- `native01/references-O0-prior-wasm.exit`
- `native01/references-O2-native-run.stdout`
- `native01/references-O2-prior-wasm.exit`
- `native01/release-verification.json`
- `native01/results.json`
- `native01/summary.json`
- `native01/tags-O0-native-run.stdout`
- `native01/tags-O0-prior-wasm.exit`
- `native01/tags-O2-native-run.stdout`
- `native01/tags-O2-prior-wasm.exit`
- `native01/unit.exit`
- `native01/unit.stderr`
- `native01/unit.stdout`
- `native01/variant-O0-native-run.stdout`
- `native01/variant-O0-prior-wasm.exit`
- `native01/variant-O2-native-run.stdout`
- `native01/variant-O2-prior-wasm.exit`
- `native02/commands.json`
- `native02/empty-O0-native-run.stdout`
- `native02/empty-O0-prior-wasm.exit`
- `native02/empty-O2-native-run.stdout`
- `native02/empty-O2-prior-wasm.exit`
- `native02/empty-native.exit`
- `native02/empty-native.stderr`
- `native02/empty-native.stdout`
- `native02/golden.py`
- `native02/lease.json`
- `native02/release-verification.json`
- `native02/results.json`
- `native02/summary.json`
- `native02/unit.exit`
- `native02/unit.stderr`
- `native02/unit.stdout`
- `pre-repair-wasm_codegen.h`
- `promoted.json`
- `reconstruction.json`
- `remaining01/adaptation-O0-reject.exit`
- `remaining01/adaptation-O2-reject.exit`
- `remaining01/argument-O0-reject.exit`
- `remaining01/argument-O2-reject.exit`
- `remaining01/assign-O0-reject.exit`
- `remaining01/assign-O2-reject.exit`
- `remaining01/checks.py`
- `remaining01/commands.json`
- `remaining01/elements-O0-reject.exit`
- `remaining01/elements-O2-reject.exit`
- `remaining01/inline-argument-O0-reject.exit`
- `remaining01/inline-argument-O2-reject.exit`
- `remaining01/lease.json`
- `remaining01/match-value-O0-reject.exit`
- `remaining01/match-value-O2-reject.exit`
- `remaining01/print-O0-reject.exit`
- `remaining01/print-O2-reject.exit`
- `remaining01/release-verification.json`
- `remaining01/remaining.exit`
- `remaining01/remaining.stderr`
- `remaining01/remaining.stdout`
- `remaining01/result-O0-reject.exit`
- `remaining01/result-O2-reject.exit`
- `remaining01/results.json`
- `remaining01/summary.json`
- `remaining01/temporary-O0-native-emit.exit`
- `remaining01/temporary-O2-native-emit.exit`
- `remaining01/unit.exit`
- `remaining01/unit.stderr`
- `remaining01/unit.stdout`
- `remaining01/value-equality-O0-reject.exit`
- `remaining01/value-equality-O2-reject.exit`
- `remaining01/variable-O0-reject.exit`
- `remaining01/variable-O2-reject.exit`
