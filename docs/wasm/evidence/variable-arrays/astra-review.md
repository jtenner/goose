Independent review of the Goose variable-array stage

No confirmed production correctness defect was found in the reviewed change. The packed layout, reference widths, call bases, and cleanup paths are consistent with the admitted scalar/reference array subset. This is a read-only review, not a full validation approval. Final validation has an unresolved setup failure and two unrun suites.

Repository: `/home/dev/Projects/goose-wasm-backend`. Baseline and observed HEAD: `660e9f68aef4187924a37037f7f017b05634d920`. Candidate compiler SHA-256: `ccb45b63e07c3dc3a80ef392e12db035453b6fd65cd7e7b4387efb5222ad464f`.

Raw evidence cutoff: **2026-11-07 06:22:55 UTC**. The continuation was pending when the packet was made. It produced records during this review. Only records read at the cutoff are counted below. No build, test, compiler, debugger, timing job, subagent, or Claude process was started by this reviewer. No production file was changed. No prior review conclusions were used.

**Confirmed validation issue, separate from production defects**

V1. Medium severity for release validation: the native suite cannot complete with the copied compiler's current bundle layout.

- Location: `test/jit_runtime.py:14-18`; caller `test/run_tests.py:2624`; evidence `constructor-repair02/native.stdout`, `native.exit`, and `lease.json` under the raw evidence root below.
- Valid trigger: the recorded native-suite command passes `--exe /tmp/goose-wasm-variable-arrays-20261107/constructor-repair/goose-tested`. The helper resolves the compiler path and searches for `tcclib/include/tccdefs.h` beside it or one directory above it, unless `GOOSE_TCCLIB` supplies a path.
- Expected behavior: the helper finds the compiler's bundle, then runs its embedded JIT checks.
- Actual behavior: the helper reports `cannot locate the compiler's bundled TinyCC files`; the native suite records one failure and exit 1. The wrapper stops, so final compatibility and equivalence suites have no result at the cutoff. Native stderr is empty; the failure is in stdout.
- Evidence: the preserved compiler and repository `build/goose` have identical hashes. The preserved copy has no adjacent TinyCC bundle; the repository build directory has `tcclib`. Inspection of the helper places this failure before its guest subprocess calls. This supports a test setup cause, not a variable-array code defect. No new run was made to prove the proposed setup correction.
- Risk: claiming the full final suite passed would be false. The first compiler's passing native suite does not replace final validation.
- Narrow action/check: use the matching repository executable in its build layout, or supply the required existing bundle path to the validation owner. Then run the incomplete native, compatibility, and equivalence checks under that owner's host lease. Keep the recorded failure. This reviewer did not change setup or run those checks, as instructed.

**Correctness and design assessment**

- Packed layout: `src/wasm_arrays.h:57-100` uses the shared unsigned prefix width, followed immediately by `Size(element)` bytes per element. The default prefix is u32. Scalar and ordinary-reference element widths match `ValueLayout::FixedSize`. References occupy eight stored bytes even when their live Wasm value is i32. Wasm memory operands use one-byte alignment hints. The C comparison used `RawArrayView`, `EmitLenStore`, `EmitArrayCount`, and `GenArrayLit`.
- Bounds and growth: the constructor checks `count <= (UINT32_MAX-prefix)/stride` before multiplying. Admitted elements have nonzero fixed size. The short-prefix bound is checked without a shift by 64. `Reserve` adds the old top and complete byte count in i64, checks the Memory32 bound, grows if needed, then publishes the top. Thus every constructor store lies inside the reservation. Direct i32 offset addition cannot wrap, and packed i64 addition cannot carry into the memory identity. Indexing adds the prefix once and preserves the high identity bits. Length is captured before an index expression with effects. Normal indexing rejects negative indices through the unsigned bound test.
- Reference interfaces: `FrameRef` keeps fixed/limited/growable array references thin. A variable-array owner and its references use i64 memory/address values. `ReferenceAddress` returns the payload address, not a pointer to the owner's local or global pointer slot. Loads and stores widen or narrow thin stored references at the correct boundary. Dynamic memory access validates the memory identity. `NoteType` now follows nested arrays and references, so an interface with no data owner still gets the required reference width and helper availability. It does not allocate an unused data memory.
- Global and scoped storage: local variable-array owners use Wasm locals; globals use a private eight-byte Memory0 pointer slot and dedicated persistent data memory. Only scoped owners register a restore. The saved top is the old top returned by reservation. Cleanup shares the existing reverse action list with deferred bodies, returns, breaks, and continues. This matches the C restore ordering. A dedicated global is outside the shared local memory block.
- Callee bases: the storage walk assigns the owner's logical stack before it visits element initializers. Calls in those initializers therefore use bases above the live owner. Conflicting incoming bases use the existing hidden base parameter. The shared `DataStackCounts` cycle rule is unchanged. The new fixtures call the same allocating function with different live-owner counts, and call allocating functions from inside constructors.
- Reference-return address paths: the new `Gen` gate accepts matching array references returned by calls and inline blocks, and references loaded from array elements. `Convert` checks null and keeps the array address. It still rejects owned array temporaries and by-value array signatures. Assignment to a whole array is rejected rather than creating an alias. Return lifetime validity still depends on the unchanged frontend checks; this review did not re-prove the whole frontend lifetime system.
- Equality: lengths are compared first, then scalar values or reference identities. Float comparison uses Wasm float equality, which preserves NaN and signed-zero behavior. C's `EqX` and byte-array equality use the same value rules for this admitted subset. An effectful right operand is still rejected where a value snapshot would be required. No widening of that unsupported operation was found.
- Iteration: mutable reference roots and reference elements on indexed paths reload at each iteration. Index expressions are evaluated once. A statement-bearing index freezes the parent view and length before its effects. `LoadArrayWalk` now allocates the local with the element reference's actual width. This matches the C path model examined in `IndexLoc`, `ForLoop::CgStmt`, and `HoldForSequence`.
- Constructor order and scratch: each element is evaluated and converted before its store, in source order. The whole payload is reserved first. One item local is reused. The fixed-memory store path does not call `StoreElement`, which would allocate another temporary per element. The dynamic path also reuses the item local. Complex initializer expressions can still require locals of their own; the bounded claim applies to constructor bookkeeping, not arbitrary input expression complexity.
- Old shared callers: direct inline/growable length access remains on Memory0; the default memory parameter preserves their old calls. Rebinding routes through the new shared address helper. Unsupported array assignments now fail explicitly. The reviewed C files are unchanged. The saved first-stage comparisons support preservation of existing output, with final-stage comparison limits stated below.

**Coverage limits and unverified risks**

These are gaps, not confirmed defects or valid reproductions of wrong behavior.

- `test/wasm_backend.py:184` checks large constant literals through fixed call bases. Small fixtures cover dynamic bases. There is no large dynamic-base constructor record. A narrow follow-up is to call a large-literal function at two live-owner depths and check output, local counts, and restored tops at O0/O2.
- The new fixtures cover normal scope reuse and return from an allocating function. They do not combine variable-array owners with every defer/early-return/break/continue exit. Existing growable-array fixtures exercise the shared cleanup mechanism, but are not direct coverage of every new owner path. A narrow follow-up is to port the ordered-cleanup fixture to variable-array owners and retain exact output plus post-completion owner-top assertions.
- The new positive fixtures do not cover every thin reference inside a variable payload, optional reference element, reference-array equality mode, or deep effect-bearing/rebinding path. The shared implementation and older fixtures were reviewed, but these combinations remain limits on execution evidence.
- Existing rejection tests mainly use growable/inline arrays. A focused variable-array rejection matrix should prove native input validity and the specific target rejection, with no output file, for whole-array copies, by-value arguments/results, owned temporaries, fills, strings, varint prefixes/elements, and unsupported mutation. No incorrect acceptance was established here.
- Whole-reservation overflow and growth failure are supported by the unchanged helper's checks and existing helper tests. The new stage's saved large case demonstrates successful growth, not a near-4-GiB variable-array allocation or failed whole-payload growth. No such new experiment was run.
- The owner checker waits for synchronous `_start` completion before it reads actual stack-top globals. Its variable-reuse and growth checks inspect guest linear-memory size. It excludes persistent global memories from the restored-top check; global lifetime is also checked through program output. It does not independently assert the exact final global top.

**Raw validation and identity assessment**

Raw evidence root: `/tmp/goose-wasm-variable-arrays-20261107`.

1. `build-check`: all 37 top-level recorded exits are zero. Records show 281 Wasm checks, the native suite with its stated skips, 52 exact compatibility comparisons, and 62 prior Wasm module pairs. I checked all 30 targeted command records, empty error output, and the Node/Wasmtime/owner output against the copied expectations. I independently compared all 62 saved before/after modules and their output/error/exit records. I also compared all 52 native/scalar artifact pairs and diagnostics and checked the saved source/output hashes. There were no mismatches. These results use the first compiler, hash `78a2f4a3db727c55869aefe1eb4e08e6f7f7f80b55095594571280555ef28476`.
2. `large-before`: the 14,000-element source is native-valid in the recorded run, with output `14000,1`. The old Wasm module has 56,015 locals. The validator says `too many locals`; Node says `local count too large`. Both record exit 1. The separate 9,000-element source records successful native/Node/validation results with output `9000,0,8999`. I checked both source hashes and every generated literal value. This is specific failing-first evidence for the excessive-local defect, not an unrelated rejection.
3. `constructor-repair`: the compiler build records exit 0. The saved 14,000-element O0 module validates and runs in Node and Wasmtime with the expected output. The owner checker then fails at the JavaScript spread into `output.push`, before guest execution. This is a checker failure. The repaired checker copies bytes in a loop. The original run did not finish its remaining suites or write a completed large-results file.
4. `constructor-repair02`: records arrived during the review. At the cutoff, both large cases at O0/O2 have emit/validation/Node/Wasmtime/owner exits of zero, empty stderr, and exact native output. I parsed each saved module's local declarations and checked its byte length and hash against the result record. The Wasm suite records **289 checks passed**, exit 0, empty stderr. The native suite records the setup failure V1, exit 1. Final compatibility and equivalence records are absent. The lease record says the validation owner stopped and reaped its children. No later result is claimed.

Exact provenance checks:

- At the initial identity check, all 21 files in `source-hashes.json` matched both the packet and repository copies. Their hashes and inspection status are listed in the file inventory.
- `git rev-parse HEAD` matches the baseline. The only working-tree changes are the 12 files in `scope.json`. `git diff` for the five tracked changes is byte-identical to `changed.diff`, SHA-256 `d91db520a1d1e4c17448ac7c824fd21e65c10513a2093b57a480529319731e98`. The seven untracked files were read from the packet and hash-matched to the repository.
- All 88 production/build entries in `build-check/source-manifest.json` were checked. Only `src/wasm_arrays.h` differs from the current candidate, as expected for the constructor repair. Harness identities were inspected separately; the test suite and checker changed between stages.
- All 4,112 entries in `constructor-repair/source-manifest.json` were checked against the repository. Only `test/wasm_multimemory.mjs` differs. At the manifest check, all 4,112 entries in `constructor-repair02/source-manifest.json` matched. These are identity checks, not semantic reviews of 4,112 files.
- Preserved first compiler: `78a2f4a3db727c55869aefe1eb4e08e6f7f7f80b55095594571280555ef28476`.
- `constructor-repair/goose-tested`, `constructor-repair02/goose-tested`, and repository `build/goose`: `ccb45b63e07c3dc3a80ef392e12db035453b6fd65cd7e7b4387efb5222ad464f`; both compiler hash records agree.
- Repository `build/goose-inline-checkpoint` and `/tmp/goose-wasm-inline-arrays-20261107/equality-repair/goose-after-review`: `63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`. This matches the compatibility reference identity. That external file was read only for its hash, not for prior review conclusions.
- Repository `build/goose-shared-services`, used by the recorded large native oracle: `c30a6d3ebd9890579c7ec854db3d018a12eca35666511e75cfa5f263b133f67f`. This is its observed current identity; the large-case identity JSON pins the Wasm compiler and sources, not that native compiler's historical hash. The final Wasm suite also builds native oracles using the preserved candidate.
- Large source hashes: `locals.goose` = `c54277832c01d24f6ab63ef243539cfcc66630a968b58e42714440d8c0e86e53`; `growth.goose` = `c9448327c83ce860d89c8b870e2de7c91562b10f718b43ee402078ac2b642489`.
- Build logs, source manifests, and binary hashes are consistent. No independent rebuild, disassembly, or reproducible-build proof was performed. The logs record ordinary compiler warnings; they do not establish a new defect in this change.

**Footprint assessment**

These are saved-module measurements, obtained by reading files and decoding local declarations. Local counts exclude parameters. No guest or compiler execution was needed for this review.

| Source | Before: bytes / maximum locals | Repaired: bytes / maximum locals |
| --- | ---: | ---: |
| 14,000 `u8[u16]` elements | 2,209,599 / 56,015 | 230,800 / 16 at O0 and O2 |
| 9,000 `i64[]` elements | 1,414,542 / 36,021 | 162,931 / 22 at O0 and O2 |

Before module hashes are `feca3c8db147e7d4572042106131c2127e29b99496df77e70e0134a35c1b35a0` and `5200e7d072e82b8ab85742030e8f6a60832aa86206a145afb46391789b1db7f4`, respectively. Repaired hashes are `b84dcfd6ddd48cb5fedd7743af8d4fff627c735bc0e2eabc71a8dc50a0033972` and `88458c43b9101a32ebf287012d43728faef4d1743615e7909b01bcdab2aeed25`.

The repair removes four bookkeeping locals per literal element and repeated address-check/trap material in these cases. Module bytes fall by about 89.6% and 88.5%. This comparison is against the first variable-array implementation, not baseline master, which did not support these constructors. The repair is narrow and the smaller local count is sufficient to remove the recorded validator failure.

Runtime construction still performs work proportional to the number of explicit elements and stores the complete payload. It makes one reservation call per constructor, with possible `memory.grow`, plus one restore per scoped owner. No per-element guest heap allocation is introduced. Dynamic reference access and dynamic allocation bases use helper calls and dispatch; fixed owners use direct indexed memory operations. Equality and iteration remain linear in the number of visited elements. Rebinding-path reloads add work per visited path step, as required by the language behavior.

Compiler output and AST traversal still grow with literal size. `Local`, emitted byte strings, storage maps, and helper generation use host allocations. Bounded constructor scratch does not mean constant compiler memory use. `NoteType` follows nested types until it finds a data-address need. Helper code size grows with the number of assigned memories, bounded by the backend's 64-data-memory limit. Adding a data-address interface can widen ordinary scalar references and route shared scalar-reference callers through dynamic helpers across the module. Old programs with no such new interface retain their old path; mixed-program runtime cost has not been measured.

Each physical data memory starts at one 64-KiB page. Scope restoration resets the top; it does not shrink linear memory. Large successful growth therefore retains the guest memory high-water capacity. The owner checker proves the current owner top after completion and the guest buffer size, not physical memory release.

The repaired JavaScript checker avoids the spread-argument limit but still copies the module into number arrays and then a `Uint8Array`. Its time and temporary host memory are proportional to module size. This is test-only work and is not a guest memory claim.

**Missing measurements:** no controlled compiler CPU time, compiler RSS, host allocation counts, guest throughput/latency, guest CPU time, runtime code-size measurements, process RSS, physical-memory residency, or platform comparison was supplied or collected. Test-suite wall times are not controlled benchmarks. Available execution evidence is Linux x86-64 with Node 24.22.2, wasm-tools 1.262.0, and Wasmtime Python 49.0.0. No ARM, Windows, macOS, browser, or other native-platform measurements are established. No general speed or physical-memory gain is approved by this review.

**Inspection inventory and unread material**

The complete path-by-path inventory is [review-file-inventory.tsv](/tmp/goose-wasm-variable-review-20261107/review-file-inventory.tsv). It lists scope files, additional context, every raw evidence file present at the cutoff, and every manifest-only file checked for identity. It includes SHA-256 and distinguishes full source review, partial source review, raw-record inspection, byte comparison, and identity-only reads. Raw evidence contents and the comparison audit are retained in [review-evidence-audit.json](/tmp/goose-wasm-variable-review-20261107/review-evidence-audit.json). Reading bytes for a hash or comparison is not reported as a full source review.

All 12 changed files were inspected in full, including the copied untracked files:

- `src/wasm_arrays.h`
- `src/wasm_codegen.h`
- `src/wasm_storage.h`
- `test/wasm_backend.py`
- `test/wasm_multimemory.mjs`
- `docs/wasm/evidence/variable-arrays.md`
- `test/wasm/wasm_variable_arrays.goose`
- `test/wasm/wasm_variable_no_owner.goose`
- `test/wasm/wasm_variable_paths.goose`
- `test/expected/wasm_variable_arrays.out`
- `test/expected/wasm_variable_no_owner.out`
- `test/expected/wasm_variable_paths.out`

The other packet sources inspected in full were `src/value_layout.h`, `src/data_stacks.h`, `src/wasm_binary.h`, `src/wasm_memory.h`, `scripts/run_wasm.mjs`, and `test/wasmtime_host.py`. Packet context read only in relevant parts was `src/ast.h`, `src/codegen.h`, and `src/codegen_builtins.h`. Their remaining content is not claimed as reviewed. The inventory gives the additional repository files and inspected line ranges.

No changed source or fixture was left unread. Generated native C artifacts were byte-compared where stated, not reviewed line by line. Saved executables were hashed, not run or disassembled. Saved Wasm was byte-compared or parsed for local counts where stated, not fully disassembled. Full per-case native-suite logs outside the four named evidence directories were not reviewed. Manifest-only repository files were checked for identity, not semantics. Evidence created after the cutoff is outside this report. These limits apply to the no-defect conclusion.

Final source recheck: the packet still matches all 21 listed hashes. All production sources and test files still match the packet. The repository copy of `docs/wasm/evidence/variable-arrays.md` changed after the initial check; its final observed SHA-256 is `3b8ac978a4974585f46b943573b5ce94a393035854ef3d5cbd2556879cf81cae`. That later document content is outside this review and was not semantically reviewed. The frozen packet document remains the reviewed version. No later validation result was added to the report.
