The frozen implementation needs two correctness changes before acceptance. One scalar field path emits an address as a value. A second path rejects a valid call whose struct-reference result is discarded. Both findings follow from the current frontend, optimizer, and emitter source. I did not compile or execute the proposed cases. The task prohibits those operations. The saved passing suites do not cover these cases.

This was a read-only source and evidence review of `/home/dev/Projects/goose-wasm-backend`, against `b4eca3b5d5379246db7921500f1cbbc28ab1b67e` on `feat/wasm-multimemory-backend`. HEAD and branch match that baseline. I used no agents, Claude, builds, compilers, tests, guest execution, debuggers, timing, or resource jobs. I wrote only this report and review notes in the required directory.

**Confirmed source defect 1: P1, load a scalar field when an explicit reference decays to a value.** Location: [src/wasm_codegen.h:728](/home/dev/Projects/goose-wasm-backend/src/wasm_codegen.h:728), especially line 731.

Valid triggering case:

```goose
struct S { x: i64 }
fn main() {
    var s: S = S { x: 7 };
    var got: i64 = &s.x;
    assert(got == 7);
}
```

Expected behavior: `got` contains 7. The explicit reference meets an `i64` destination, so it reads the field. This is ordinary fixed scalar field access, within the admitted subset.

Source proof:

- `docs/goose_spec.md:728` and `:1213` require reference transparency in value contexts. `TypeCheck::CheckValue`, `src/typecheck_exprs.h:1001`, decays the reference and records the scalar expression type at line 1015.
- `Unary::Opt`, `src/optimize.h:1147`, keeps address-of expressions. Its default case does not fold `&`. The field remains a stored field at O0.
- The new field branch checks whether the **stored field** is a reference. Since `s.x` stores an integer, it calls `PlaceAddress(place, Type(n->exprtype), ...)`. `Type(i64)` is the Wasm i64 type.
- `PlaceAddress`, `src/wasm_fixed.h:50`, adds the field offset and extends the Memory 0 address to i64. It emits no load. The variable initializer then stores that address as `got`. A live frame address cannot be 7: zero is reserved and the initial frame top is aligned above the static prefix.
- Native `Unary::CgX`, `src/codegen_nodes.h:82`, explicitly uses `LoadLoc` when the expression type is no longer a reference. The adjacent Wasm index and identifier branches also handle value decay.

Risk: silent wrong integer results in valid programs. The same branch can give a false bool field a nonzero address value. A float destination receives an integer address instruction instead of a float load, so the emitted module can fail validation. These latter variants are source deductions, not recorded execution results.

Suggested narrow fix: in the address-of-field branch, distinguish an actual reference result from a scalar value result. For a non-reference scalar result, read the field with `ReadPlace` and convert from its stored type. Preserve array-address handling and the prohibition on aggregate scalar values. Keep the existing stored-reference behavior.

Discriminating tests: first record the case above failing on this frozen compiler, then passing after the fix. Cover integer widths, false bool, f32/f64, nested fields, a struct-reference receiver, and a field that itself stores a reference. Run at O0/O2 with thin and packed ordinary references. Validate the modules as well as their values. Check that explicit reference bindings still preserve identity. The fix should add only the load needed by the language, with no new heap allocation.

**Confirmed source defect 2: P2, discard ordinary struct-reference call results in their declared representation.** Location: [src/wasm_codegen.h:963](/home/dev/Projects/goose-wasm-backend/src/wasm_codegen.h:963), with the rejection at line 681.

Valid triggering case:

```goose
struct S { x: i64 }
recursive fn touch(s: S&) -> S& {
    s.x += 1;
    return s;
}
fn main() {
    var s: S = S { x: 7 };
    touch(s);
    assert(s.x == 8);
}
```

Expected behavior: call `touch`, keep its mutation, and discard its reference result. This requires no by-value aggregate ABI or aggregate temporary. At least O0 must accept it under the stated struct-reference parameter/result support.

Source proof:

- `TypeCheck::CheckStmtExpr`, `src/typecheck_flow.h:2488`, uses `CheckValue(n, nullptr)`. `CheckValue`, `src/typecheck_exprs.h:993`, decays the plain `S&` result to the `S` expression type.
- O0 does not inline the call (`src/optimize.h:42`). Its mutation prevents elimination as a pure discarded expression.
- `Statement` handles this mismatch only for builtins B_PUSH and B_POP. The ordinary call falls through to `Gen(n)`.
- `Gen`, `src/wasm_codegen.h:681`, rejects a struct expression when no result-type override is supplied. It never reaches `CallValue`, which already supports emitting the declared reference result.
- The saved `diagnosis01/push-O0-wasm.stderr` records the same class of rejection for a discarded push. The repaired push path and its later passing record do not exercise an ordinary call.

Risk: valid effectful calls are rejected within the advertised reference-call subset. This is an admission failure, not evidence of memory corruption.

Suggested narrow fix: handle discarded calls by their actual single reference result, including direct calls and retained inline calls. Emit that reference and drop it. Keep all live by-value aggregate call guards. Do not remove the general struct-value guard.

Discriminating tests: first record the direct O0 case failing with the aggregate-value diagnostic. Then cover O0/O2, an explicit inline function, a retained InlineBlock, and a function-value call where valid. Assert the mutation and call count, not only successful compilation. Keep separate used-result copy/identity and discarded push/pop tests. There should be no aggregate copy or new runtime allocation on the discarded path.

**Design assessment.** The place-based design is suitable for this stage. `FixedPlace` keeps the stored type, address, memory identity, and offset separate. Struct owners reserve Memory 0 storage. `ActualType` prevents the checker-adapted expression type from authorizing a differently laid-out copy. The field receiver check also rejects nominal accessor adaptation. Ordinary reference fields use eight stored bytes even when their current Wasm representation is i32.

I found no further confirmed error in the reviewed offset, null, copy, or cleanup paths. `PointeePlace` checks null before field selection. Known-memory loads use a Wasm memarg offset, whose effective address does not wrap as i32 arithmetic would. Unknown packed addresses check the low-address addition before restoring the memory identity. Bounded owner offsets are covered by checked frame/global reservations. Field assignment captures the receiver and, for pointee assignment, the stored reference before RHS effects.

The struct constructor walks checked initializers in declaration order with a monotonic initializer index. The frontend sorts and validates that order. Nested copies finish before later initializers. Byte copies preserve reference targets and do not rebase them. Defaults use the checked default tree; optional missing fields are zeroed. Filled scalar/reference arrays capture their fill value once, including zero-count fills. The reviewed push code captures the item before reading the current length, so RHS appends are included. Pop captures its element before publishing the reduced length/top.

`WasmValueSupport::Check` uses a work list and a seen set. It commits the validated set only after the entire reachable graph and bounded fixed sizes pass. References terminate stored-size recursion but not support validation. `NoteType` follows references and struct fields to find hidden data-address requirements. The checked size cache checks each caller's limit. Child products are checked before `LayoutFields` uses `FixedSize`; field sums and alignment additions use the bounded path. Frame sums, static sums, and runtime frame growth have separate checks. Unsupported shapes remain subject to the observed admission guards, including inline argument bindings and retained call results.

The shared native interface remains source-compatible: the added `LayoutFields` parameters have defaults, and native callers use the unbounded path. `CodeGen::EmitCFields` still uses that interface. The main driver includes the new headers and emits Wasm only after frontend, optimizer, and BCE work. Output is written only after `Run` succeeds. I found no native interface change that requires a new platform implementation. This is source evidence plus the saved Linux validation, not cross-platform execution evidence.

**Cost assessment and unverified risks.** The following are limits or follow-up work, not additional confirmed functional defects.

- The new support sets, size cache, storage maps, and layout vectors allocate compiler memory. Retained entries scale with reachable types, fields, and owners. The layout map uses ordered-map lookup, so its lookup cost is logarithmic in cached nominal layouts. The graph walk itself visits each reachable type once per uncached validation batch. This is not a measured compiler CPU/RSS/allocation result.
- Field-path lookup repeats work: `FieldPlace` first resolves its parent path, then `ActualType(field)` walks the path again (`src/wasm_fixed.h:143` and `:150`). A chain of depth D can therefore perform O(D squared) type-path work for one field access. The frame/address instructions remain proportional to the path. No saved depth-scaling measurement establishes the practical cost. Reusing the resolved struct instance's selected field type is a narrow possible improvement after a measured case establishes need.
- Literal field lookup is linear in the number of fields and initializers. Scalar literal code remains proportional to the number of expressions. The limited-field constructor reuses six scratch locals. The 32/256-element constant-integer probes show a bounded local count, not a bound for arbitrary effectful initializer expressions, which can allocate their own compiler-generated locals.
- The saved footprint result is specific: main-function locals fall from 116/788 to 22/22 for 32/256 elements. Module bytes fall from 8,876/66,403 to 8,812/64,347 at both optimization levels. Per-element stores, capacity/offset checks, and failure-site data still increase code size with literal length. This result does not prove runtime speed or minimum footprint.
- A packed struct-reference copy can select the shared dynamic `Copy()` helper through `ConstructFixed` and `CopyBytes`. `src/wasm_memory.h:191` emits a memory-pair dispatch table with O(M squared) code for M memories, bounded by the backend's 65 total memories. Dynamic scalar accesses use O(M) helper code. These helpers are shared, but the constructor footprint probes do not measure this high-memory-count case. Current struct owners all reside in Memory 0, so preserving that provenance could reduce dispatch after separate validation. No speed gain is claimed here.
- Frames reserve the sum of bound slots per activation and do not reuse lexical slots. Normal function exits restore the frame top after cleanup. Memory pages remain allocated after growth. Global sparse capacity increases guest minimum memory while `ZeroData` avoids a compiler byte string and serialized zero payload of that size. Fixed copies take work proportional to copied bytes. No new aggregate guest heap or host call is introduced.
- The saved fixtures do not directly cover inline **reference-array fields** using the new constructor scratch path. The reference fixture uses standalone arrays; the array-field fixture uses scalar elements. Add a nested/global field case with targets in distinct data memories, exact copy, rebinding, and used/discarded push/pop results. Assert target identity and neighboring fields. This is a coverage gap for the admitted surface, not proof that the implementation is wrong.
- No new compiler CPU, RSS, allocation, guest-time, or retained-physical-memory samples exist for this stage. No native cross-platform execution is established. The complete dispatch/layout/exception/worker matrix remains absent. Any cost acceptance needs the queued coordinated measurement turn against master and the exact prior compiler, including shared native layout callers. I did not obtain a resource lease or run measurements.

**Evidence checked.** All 30 manifest files matched their hashes before review. The scoped tracked diff also matched `tracked-diff.json` exactly. The final verification result is recorded below and in the linked notes.

The three preserved compiler binaries match their recorded SHA-256 hashes:

| State | Compiler SHA-256 |
| --- | --- |
| build01 | `59426cd40cfc85ecede3a6121697c7041387e3b7bc0c884393a90aa65472fa68` |
| build02 | `13d228e3e7b7390fcd5f97deb76185c49111128ef8b0e74d4147ecfaf52fad63` |
| build03 | `64597883981261b8a72ef3b21cb9caf1e1e67861ceb8203ecc517076de228530` |

I checked all nine reconstructed source texts against their original build hash manifests and reviewed the changes between the three states. The final three texts equal the reviewed source. The freeze scripts check source hashes before preserving the compiler. I inspected build commands, exit records, and warning output. I did not rebuild or independently prove the binaries' provenance beyond these preserved records and hashes.

The archive's 1,231 record entries match their raw files exactly; none of those entries is missing. I checked command/result records, original errors, corrected inputs, targeted stdout/stderr/exits, admission results, control results, and harness logic. The 42 `test02` Node/Wasmtime/owner stdout records match the seven exact expected files at O0/O2, with zero exit and empty stderr. They use build02. The final build03 full-suite record uses the checked-in harness and records exit 0, empty stderr, and `548 checks passed`. All 122 modules listed in `final-modules.json` match their saved binary hashes. The final suite is an aggregate transcript, not a full per-subprocess success transcript. Its count combines executions, admission checks, and static checks.

The wrong-width control first validates a module with the selected store widened, then fails at the specific neighboring-field assertion on line 14 in both engines and at both optimization levels. Its stdout matches the required prefix. This is useful evidence that the packed-width assertion detects that error. The completion harness waits for the synchronous `_start` return, then checks the owners' frame/data tops and pending print state. The frame-growth case checks actual memory size. These observations do not establish OS RSS or page release.

The initial push diagnosis has an unchanged input in diagnosis01/diagnosis02, an aggregate-value diagnostic before repair, and successful compilation after repair. The later targeted and full suites exercise the resulting behavior. Initial admission failures included invalid native inputs and a wrong expectation that an optimized fresh literal must be rejected. The corrected harness separately accepts the optimized literal and checks the remaining exact diagnostics. These corrections are not production bug fixes.

The full native baseline records success on Linux x86-64, with gcc 14.2.0 and TinyCC, plus the required clang checks. Its skips include 23 device/layer tests, transparent huge pages, the Windows commit-limit test, 36 unsupported JIT tests, two JIT samples, and five device samples. Those skips remain limits. The recorded wall-clock total is not a controlled performance sample for this change.

I independently compared all 52 saved C/report/diagnostic/older-Wasm pairs and all 100 prior-module pairs, including their saved stdout, stderr, and exit files. All match. The 52 comparisons use the older preserved inline checkpoint (`63ce6ebe...`), while the 100 pairs use the prior varint-prefix compiler (`6f110d8e...`) and build03. These are exact byte comparisons, not 152 independent native executions or a performance comparison against master.

I read `evidence-record-notes.md`, both original wrappers, `oracle02/record-correction.json`, and `oracle02/release-verification.json`. The second wrapper demonstrably retained the oracle01 output path. The original oracle01 aggregate lease/stdout/stderr/exit files were overwritten and are unavailable. Their current contents must not be described as the original first attempt. The original per-case records and first release record remain. The copied second aggregate files and correction record describe their origin. The later release record reports the actual deferred exclusive probe after the other owner released. Its `exit: 1` is consistent with the oracle unit's failed input checks; it must not be treated as a successful oracle run. The notes also disclose the premature probe claim and masked verifier failure. I did not reconstruct lost records, repeat the probe, or infer any performance sample from these records.

**Inspected scope.** Every file in the exact 30-file manifest was inspected. For `src/main.cpp`, semantic inspection covered its changed includes and frontend/optimizer/BCE/backend routing; unchanged unrelated driver features were outside this review. Other listed implementation files, fixtures, expected files, and harnesses were read in full. Report files were read in full.

- `CMakeLists.txt`
- `docs/wasm/evidence/fixed-structs.md`
- `docs/wasm/status.md`
- `src/main.cpp`
- `src/value_layout.h`
- `src/wasm_arrays.h`
- `src/wasm_binary.h`
- `src/wasm_codegen.h`
- `src/wasm_fixed.h`
- `src/wasm_storage.h`
- `src/wasm_support.h`
- `test/expected/wasm_struct_arrays.out`
- `test/expected/wasm_struct_calls.out`
- `test/expected/wasm_struct_cleanup.out`
- `test/expected/wasm_struct_effects.out`
- `test/expected/wasm_struct_hidden.out`
- `test/expected/wasm_struct_refs.out`
- `test/expected/wasm_struct_values.out`
- `test/wasm/wasm_struct_arrays.goose`
- `test/wasm/wasm_struct_calls.goose`
- `test/wasm/wasm_struct_cleanup.goose`
- `test/wasm/wasm_struct_effects.goose`
- `test/wasm/wasm_struct_hidden.goose`
- `test/wasm/wasm_struct_refs.goose`
- `test/wasm/wasm_struct_values.goose`
- `test/wasm_backend.py`
- `test/wasm_fixed_layout.cpp`
- `test/wasm_multimemory.mjs`
- `test/wasm_struct_admission.py`
- `test/wasm_struct_checks.py`

Relevant supporting source inspected: `docs/goose_spec.md` sections 3.8, 4.1, 4.2 and construction rules; `src/typecheck_exprs.h` reference decay, AutoRef, CheckValue, and CheckInits; `src/typecheck_flow.h` statement checking; `src/typecheck_nodes.h` scalar/reference/literal checking; `src/ast.h` field/initializer metadata; `src/optimize.h` path handling, Unary::Opt, and O0 policy; `src/codegen_nodes.h` native address-of lowering; `src/codegen_types.h` shared LayoutFields caller; `src/codegen_construct.h` native struct construction; `src/wasm_memory.h` reservation, access, and copy helpers; and `test/backend_shared.py`. These are focused reads, not whole-file audits of all shared/compiler code.

Evidence archives inspected under `docs/wasm/evidence/fixed-structs`: `scope.json`, `functional-records.json`, `controls-and-harnesses.json`, `reconstructed-compiler-sources.json`, `footprint.json`, `final-modules.json`, and `evidence-record-notes.md`. The review packet's `scope.json`, `tracked-diff.json`, and `raw-evidence.json` were also inspected.

Raw harnesses and source inputs were inspected in oracle01, oracle02, build01, build02, build03, test01, test02, diagnosis01, diagnosis02, admission01, admission02, limits01, qualification01, footprint01, footprint02, and compatibility01. This includes the original and corrected golden/unit scripts, freeze scripts, targeted scripts, admission scripts, wrong-store control, footprint scripts, equivalence script, `golden.py`, `resource-unit.py`, and `remaining-checks.json`. Compiler manifests and identities were read for all three builds. The full list of raw transcript files checked is in [transcript-files.txt](/tmp/goose-wasm-fixed-struct-review-20261107/transcript-files.txt). The exact comparison file list is in [comparison-files.txt](/tmp/goose-wasm-fixed-struct-review-20261107/comparison-files.txt).

Review notes: [hash and comparison checks](/tmp/goose-wasm-fixed-struct-review-20261107/hash-and-comparison-notes.json), [transcript audit](/tmp/goose-wasm-fixed-struct-review-20261107/transcript-audit.json), and [final module hashes](/tmp/goose-wasm-fixed-struct-review-20261107/module-hash-notes.json).

**Unread or unavailable evidence.** No manifest file or referenced archive is unread or unavailable. The overwritten original oracle01 aggregate records are unavailable as described above. No new execution record exists for the two review findings. No new CPU/RSS/allocation/guest-time samples, architecture matrix, or cross-platform runtime results are available. Saved generated C/Wasm comparison artifacts were checked as bytes and hashes, not all re-reviewed instruction by instruction. Existing qualification WAT was inspected through its control sites and recorded output, not as a full instruction audit of every function. Native executables were not executed or disassembled. Files outside the named evidence units and relevant shared callers were not inspected. A guessed `test02/check.py` path did not exist; the actual harness is `test02/targeted.py`, which was inspected. None of these limits is treated as passing coverage.

Final verification: all 30 scope hashes still match. No scoped source changed during review. See [final hash records](/tmp/goose-wasm-fixed-struct-review-20261107/final-scope-hashes.json) and the [file inventory](/tmp/goose-wasm-fixed-struct-review-20261107/inspection-inventory.txt). The inventory includes source reads, record reads, and byte/hash checks; it does not imply a full semantic audit of generated artifacts.
