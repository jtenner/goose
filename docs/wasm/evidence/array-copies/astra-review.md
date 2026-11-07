Goose same-layout array-copy constructor stage review

Review date: 2026-11-07. Repository: `/home/dev/Projects/goose-wasm-backend`. Branch: `feat/wasm-multimemory-backend`. Baseline: `5d03e3921cfdc250c578c3d63f8479dfc7e1b2a1`.

**Assessment: changes are required.** I found one correctness defect and one failure to enforce the stated stage restriction. The supplied tests support the main same-layout paths. They do not cover the two findings below. The memory-copy helper has a sound control structure on inspection, with supplied functional evidence at the 65-memory limit. Performance and minimum memory use are not established.

This was an independent, read-only review. I did not build, compile, run tests, execute guest modules, debug, benchmark, acquire a lease, contact other threads, or use another reviewer. I only read files, compared file contents and hashes, and read binary section metadata. This report is the only file I wrote. The findings are confirmed by source inspection, not by a new execution. The example programs below have not been run in this review.

**Finding 1: P1, the exact-layout check uses the adapted expression type instead of the source storage type.**

Location: [src/wasm_arrays.h:91](/home/dev/Projects/goose-wasm-backend/src/wasm_arrays.h:91), with the size selection at line 98 and copy at line 139. The shared paths that permit this are `ArrayType` at line 8 and `WasmCodeGen::Convert` at `src/wasm_codegen.h:175`.

A valid Goose input is:

```goose
fn main() {
    var a: u8[3] = [1, 2, 3];
    var b: u8[..4] = a;
    print(b.len, ",", b[0]);
}
```

Native construction gives length 3 and first element 1. This stage must reject the layout adaptation with a destination-lowering diagnostic. The new path instead emits a raw five-byte copy from the three-byte fixed source. The first source element becomes the destination length prefix. The predicted result is length 1 and first element 2. The read also extends beyond the source object. A Wasm memory bounds check does not catch an object over-read that remains within Memory0.

Evidence and reachability:

1. `TypeCheck::CheckValue` calls `MustFit` and then writes `v.type` to `n->exprtype` at `src/typecheck_exprs.h:1015`.
2. The array adaptation case at `src/typecheck_exprs.h:1300` accepts matching element types for a non-fixed destination and sets `v.type = dt` at line 1315. A fixed source can be copied implicitly. The destination capacity in this example is sufficient.
3. `ArrayType(source)` reads this adapted `exprtype`. Thus the new `TEq(array, from)` check succeeds even though `Ident::vdef->type` still describes `u8[3]` storage.
4. `Gen(Ident)` reads the original slot, then calls `Convert(actual, n->exprtype)`. Both array types use I32. `Convert` checks their Wasm value types but does not reject their different array layouts.
5. `InitArrayCopy` uses `Size(u8[..4])`, which is five bytes, and copies the fixed source address without creating a length prefix or checking the source object's size.

This is an existing, valid language conversion. The supplied native compatibility fixture has the same conversion at `test/codegen/limited_array_adaptation.goose:42` through line 46. Its saved generated C explicitly copies the elements and writes the new length. The compatibility evidence checks native generated output, so it does not test rejection by the Wasm backend.

Risk: silent wrong values, invalid length metadata, and reads from adjacent guest objects. Direct conversions between static-limited capacities can also pass this check. Other I32 array representations can reach the same unsafe conversion path. Explicit `copy(a)` often avoids this defect because its argument keeps the original source type; that does not protect implicit construction.

Narrow fix: establish the source's actual storage layout before selecting its header, size, or memory. For an identifier, use its declared storage type and remove ordinary reference layers. Use the equivalent storage/result type for other admitted source forms. Reject any unequal layout before emission. Do not implement adaptation as part of this fix. A shared array conversion guard may be useful, but it needs tests for every caller it changes.

Required checks: first reproduce the example on the current revision. Then require a specific destination-lowering diagnostic and no output module at O0 and O2. Add direct and reference-source cases for fixed-to-limited, different limited capacities, and changes in prefix width. Keep positive same-layout implicit and explicit copies. The existing tests do not provide failing-first evidence for this defect.

**Finding 2: P2, inlining bypasses the by-value array-argument restriction.**

Location: [src/wasm_arrays.h:357](/home/dev/Projects/goose-wasm-backend/src/wasm_arrays.h:357). The shared caller is `src/wasm_codegen.h:818`; the out-of-line restriction is at line 931.

A valid input that reaches the missing gate when inlined is:

```goose
inline fn first(a: u8[3]) -> u8 { return a[0]; }
fn main() {
    var a: u8[3] = [1, 2, 3];
    print(first(a));
}
```

The stated stage contract requires a diagnostic for by-value array arguments. The out-of-line path checks that contract. The inlined path does not.

Evidence: `Inliner::BindArg` creates a `VarDecl` containing the source argument at `src/optimize.h:739`. `TryInline` marks it with `inline_arg = true` at line 840. The copied variable has `isparam = false` at line 705. Wasm `Statement` ignores `inline_arg` and routes the declaration to `InitArray`. The new nonliteral path then permits a same-layout copy from the caller's array. There is no array-parameter check in `Gen(InlineBlock)`. The small scalar-result function above meets the inliner's rules. Once its call is removed, the live out-of-line signature check does not protect the argument binding.

Risk: target admission changes with the optimization level. This silently expands the stage to a calling path that the user explicitly excluded. I found no separate wrong-value result for this exact same-layout example; this finding is a restriction and coverage defect.

Narrow fix: reject an array-valued `VarDecl` marked `inline_arg` before array initialization, or check the retained inline specialization's parameter types at the Wasm admission boundary. Preserve ordinary local array-copy declarations. Add a native-valid argument test that must fail for the by-value restriction at both O0 and O2. Include a case with `copy(a)` for a non-fixed parameter if that path is included in the guard. No new execution evidence is available for this finding.

**Correctness and design observations.**

For sources whose actual storage layout matches the destination, the main copy sequence is consistent with the intended design:

- Fixed and static-limited owners stay in Memory0. Static-limited copies include the stored length and the full capacity. Zero-size fixed owners still have distinct frame slots.
- Variable arrays copy their length prefix and live elements. Runtime-limited arrays copy both U32 fields and all capacity slots. Growable arrays get a new Memory0 header and a separately allocated element run. Their copied length is stored in the new header.
- The non-inline byte calculation checks the unsigned count against `(UINT32_MAX - prefix) / stride` before multiplication and I32 conversion. Admitted scalar and ordinary-reference element sizes are nonzero. `Reserve` checks the old top plus byte count in I64 and publishes the new top only after successful growth. The existing top representation cannot use an exclusive end of 2^32.
- Source evaluation occurs once through `ArrayHeader`. Count and base are captured before destination reservation. Guest offsets and memory identities remain valid across `memory.grow`; no host buffer address is retained. No user call occurs between those captures and the copy.
- Ordinary reference elements are copied as stored address bits. The new owner has separate storage, while referents keep their identity. The variable-reference fixture checks both mutation through the copied reference and identity equality.
- Static source and destination identities use one concrete-index `memory.copy`. The fallback selects concrete indices. No host copy import is added. Byte-print snapshot imports serve output handling, not construction.
- `Type` rejects direct compound elements, resizable-header reference elements, relative references, unsupported pointee layouts, and varint layouts. `InitArray` rejects reusable pool owners. Whole-array assignment remains rejected in both variable and indexed-pointee paths. The `Gen` temporary-result gate and live result-signature gate still reject array-valued results in the reviewed paths. The two findings above are exceptions to the intended admission controls.
- The storage plan counts live owners before it emits code. It separates globals from scoped owners and rejects more than 64 data memories, plus Memory0. Calls and deferred bodies receive conservative stack offsets. A copy adds a scoped restore action after reservation; normal completion, return, break, and continue use the shared reverse cleanup sequence. Global copies do not add a scoped restore. The source checker remains responsible for reference lifetime validity.
- The new helper cache stores its function index before generation. All imports and the memory count are fixed before helper emission. `Save` resolves the function by index, so vector growth does not leave a stale function reference. The nested `Dispatch` bodies close before the outer branch is emitted. Each successful inner branch exits its own result block, then the outer branch exits the outer result block. Invalid selectors trap. The 65-memory matrix supplies execution evidence for the deepest generated control structure.
- `memory.copy` supplies overlap-safe copy and range-check behavior. The helper tests check both overlap directions, invalid identities, source and destination bounds failures, and unchanged destination bytes after the tested bounds failures. These helper checks do not prove the source-layout gate in the constructor.

I found no additional confirmed defect in helper indexing, nested branch depth, exact-layout capacity handling, or owner restoration. This is not proof for untested source forms.

**Evidence checked.**

The repository HEAD and branch match the scope file. All 25 packet file hashes match `review-source-hashes.json` and `source-manifest.json`. The live files in the source manifest also match. All four baseline production copies match the exact baseline commit. The working tree has the stated 16 changed files.

The preserved new compiler and `build/goose` both hash to `aab71c210ca140970a27e55598d8afcc156704cda25063b30ad13474851073ec`. The preserved prior compiler hashes to `fbbf0e36f41b37614c9b1f48e7f61502c0ae215b44ea6710eaa212d9b5bd9389`. The six targeted module hashes match `targeted-results.json`.

I checked all six targeted native outputs against the packet expectations, and checked each Node, Wasmtime, and completed-owner output against the same expectation. They match. The six prior-Wasm runs have exit 1 and the expected pending-constructor diagnostic. Other top-level recorded exits are zero. The build log contains warnings, but no recorded build failure.

`wasm.stdout` reports 395 checks passed; `wasm.stderr` is empty and `wasm.exit` is zero. I read the full harness to determine what those checks assert. The full-run log is a summary, not a separate raw record for each internal subprocess. The test count alone is not coverage proof.

I independently compared the saved artifacts and paired diagnostics for all 84 prior-Wasm equivalence records and all 52 compatibility records. They match their summary hashes and have zero recorded exits. The compatibility set contains 34 native C/report comparisons and 18 older Wasm comparisons. These are exact output comparisons, not new execution or performance results. The paired warning text is also equal.

I read `validate.py`, `lease.json`, and `release-verification.json`. They record successful commands, completed child cleanup, and a released lease. I did not probe the lease or repeat any command. The source/build records and hashes are consistent; I did not rebuild the compiler to establish a new independent build provenance record.

**Coverage gaps and unverified risks.**

- No Wasm negative test covers implicit layout adaptation or the inlined by-value argument gate. These omissions allow the confirmed findings.
- The three new fixtures do not count an effectful copy source's evaluations. The borrowed-source functions only return their argument. Add a source call or index that increments a counter, changes a mutable alias, and uses temporary owner storage.
- There is a global source, but no global destination constructed by copying another owner. Static and dynamic global-initializer paths need direct checks.
- There is no new constructor case for an indexed array-reference source, an optional reference after narrowing, or references to elements in another data memory. Helper byte patterns do not cover those pointer paths.
- Constructor payload coverage uses U8, I64, F64, and ordinary I64 references. It does not cover every scalar width, Boolean, F32, nonempty U64-prefixed variable arrays, or static-prefix width boundaries.
- Cleanup tests check return, break, continue, deferred copies, and final tops after synchronous `_start` completion. They do not exercise an early exit during source evaluation or a failed destination growth during copy construction. A final-top check alone cannot prove every intermediate restore order. The deferred reads provide useful additional evidence.
- The helper matrix tests every memory pair with four bytes and tests a zero-length end-of-memory copy. It does not test all byte lengths, high unsigned offsets, or every invalid selector. The constructor fixtures do not approach the memory-count limit.
- There are no deliberate broken-copy controls for the new semantic fixtures. The prior compiler's rejection proves the feature was absent; it does not prove that each assertion detects a specific wrong-copy implementation.

**Runtime, compiler, and memory costs.**

Let B be the copied byte count and M the module memory count. The constructor emits one bulk copy of B bytes, with bounded scalar work around it. Fixed/static-limited copies use the full static size. Variable/growable copies scale with length. Runtime-limited copies scale with capacity, even when length is small. This matches the saved native runtime-limited constructor, but can make a sparse-capacity copy expensive.

Known memory indices avoid a helper call. A dynamic copy executes an outer and inner `br_table` and one copy instruction. The emitted path does not scan all M squared pairs at runtime. Engine dispatch, bulk-copy, and growth costs were not measured.

The shared two-identity helper emits M squared copy cases. Its generation work and code storage therefore grow quadratically with M, bounded here by M <= 65. The first dynamic copy pays this module-wide cost; later calls reuse the helper. Even one known identity currently uses this full helper when the other identity is dynamic, except for the Memory0-source specialization. Per-destination helpers or reachable-pair pruning could reduce code size, but their added complexity needs measurement before adoption.

Static observations from the saved modules are:

| Artifact | Module bytes | Memories | Maximum function locals | Two-identity helper body bytes |
|---|---:|---:|---:|---:|
| values O0 / O2 | 22,123 / 22,111 | 18 | 390 / 392 | 6,436 |
| inline O0 / O2 | 2,239 / 2,225 | 1 | 76 / 78 | absent |
| cleanup O0 / O2 | 6,467 / 6,467 | 5 | 88 / 88 | 638 |
| three-memory helper module | 3,269 | 3 | 3 | 286 |
| 65-memory helper matrix | 112,340 | 65 | 3 | 78,158 |

Helper body sizes include local declarations and the final end opcode. The full helper modules contain other runtime functions. These are module-size observations, not runtime native-code sizes or timing gains. The old compiler rejects the new fixtures, so these fixture sizes are not before/after optimization deltas.

Copy emission uses a bounded set of locals per constructor, independent of element count. It still allocates compiler containers: local entries, cleanup actions, argument vectors from `ValueArgNodes`, helper strings, and module buffers. `ValueArgNodes().at(0)` creates a temporary vector for the copy wrapper. Type/layout checks also repeat along the source path. No compiler allocation or CPU samples establish the cost of these operations. Source expression cost is additional.

Each data memory starts with one 64 KiB guest page. Reservations advance the assigned top; growth rounds the required end to pages. Restoring a top permits reuse but does not shrink the memory. Inline copies use frame storage. Runtime-limited copies reserve and touch capacity bytes, including unused slots. Guest pages, logical tops, and distinct memory buffers do not establish physical committed memory, RSS, virtual-address reservations, or peak host memory. The new copy path has no explicit host staging buffer; engines still have their own allocation costs.

No controlled runtime CPU, compiler CPU, RSS, allocation, or native-code-size measurements were supplied. There are no raw performance samples, control runs, or architecture comparisons to assess. Functional timeouts and guest page checks cannot establish speed, a minimal footprint, or a cross-platform runtime result. Any performance approval needs separate measurements with exact build identities and the required coordinated host window. This review did not perform that work.

**Inspected files and limits.**

I read all 16 changed files in full, including unchanged surrounding code:

- `src/wasm_arrays.h`
- `src/wasm_binary.h`
- `src/wasm_codegen.h`
- `src/wasm_memory.h`
- `test/expected/wasm_array_copy.out`
- `test/expected/wasm_array_copy_cleanup.out`
- `test/expected/wasm_array_copy_inline.out`
- `test/wasm/wasm_array_copy.goose`
- `test/wasm/wasm_array_copy_cleanup.goose`
- `test/wasm/wasm_array_copy_inline.goose`
- `test/wasm_backend.py`
- `test/wasm_copy_matrix.mjs`
- `test/wasm_copy_matrix.py`
- `test/wasm_memory.cpp`
- `test/wasm_memory.mjs`
- `test/wasm_memory.py`

I compared the four baseline production files and `source.diff`. I read all of `src/value_layout.h`, `src/wasm_storage.h`, `src/data_stacks.h`, `test/backend_shared.py`, `test/wasm_multimemory.mjs`, `test/wasmtime_host.py`, and `scripts/run_wasm.mjs`.

I read relevant definitions and callers in `src/ast.h`, `src/codegen_construct.h`, `src/codegen_values.h`, `src/typecheck_exprs.h`, `src/typecheck_builtins.h`, `src/typecheck_types.h`, and `src/optimize.h`. This covered storage/type equality, argument nodes, native construction, native indexed locations, implicit adaptation, copy checking, reference validation, and inline argument binding. I also read `test/codegen/limited_array_adaptation.goose`, `test/codegen/copy_slot_layouts.goose`, and the existing `wasm_inline_effect_path`, `wasm_inline_nested_path`, and `wasm_variable_paths` fixtures. Additional repository context matches the frozen source manifest.

Evidence read includes the scope and hash manifests, compiler hashes, golden identities/results, targeted results, orchestration scripts, top-level raw stdout/stderr/exit files, lease/release records, both comparison summaries and their paired artifacts/logs, and static section metadata from the eight supplied Wasm files. I inspected the relevant generated C constructor portions in `values-O0.c` and the native limited-array adaptation output.

No changed file or listed packet context file is missing. I did not read unrelated portions of the large AST, checker, optimizer, and native code-generation headers. I did not semantically inspect every generated C line, disassemble every Wasm instruction, or read every unrelated fixture invoked by the full harness. Binary hash comparison is not semantic inspection. The full harness lacks per-command raw logs in its saved summary. New failure reproductions, controlled performance data, and physical-memory measurements remain unavailable under this review's execution restrictions.
