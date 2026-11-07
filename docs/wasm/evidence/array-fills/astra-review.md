Independent fill-constructor review, 2026-11-07

No confirmed correctness or design defect was found in the reviewed change. The implementation is narrow and uses the existing layout, memory, conversion, and cleanup rules. Source inspection shows bounded constructor scratch and generated code with respect to the fill count. The evidence does not establish runtime speed, compiler cost, or physical memory use.

This was a read-only review of production files. I ran only file reads, Git inspection, hashing, byte comparisons, and saved-module parsing. I did not run a compiler, build, test, debugger, benchmark, or guest module. I did not use agents or Claude, and did not read earlier review conclusions.

Scope and provenance

- Repository: `/home/dev/Projects/goose-wasm-backend`.
- Baseline and live HEAD: `7744624b3013ce6952a1ad9cfb0e5db683416fdd`.
- The candidate is an uncommitted change over that baseline. Git status contains exactly the three modified tracked files and four new fixture/expected files listed in `scope.json`.
- I read `evidence-guide.md`, `scope.json`, `source-hashes.json`, and `changed.diff` first. The saved diff equals the live tracked diff against the exact baseline. The four new files are not in that diff; I read them from the frozen source packet.
- All 20 frozen file hashes match `source-hashes.json`. All 20 live files match the frozen files. All 13 context files match the baseline. All 4,112 entries in the build-stage `source-manifest.json` match the live files, with no missing file.
- Candidate `goose-tested` and live `build/goose` both have SHA-256 `668f2d0c863823789a1b6fc04dac145e49996602fc79641950ea69f0cb570ffb` and size 6,996,392 bytes.
- The prior compiler used by the golden and equivalence scripts has SHA-256 `ccb45b63e07c3dc3a80ef392e12db035453b6fd65cd7e7b4387efb5222ad464f` and size 6,992,072 bytes. It matches `scope.json` and `golden-identities.json`.
- The compatibility script uses a separate, older inline checkpoint, SHA-256 `63ce6ebec6c5857c61d85270f2393c324d60b40abd4ae67b31eb19d1c656781a`. I checked that executable against its summary. The 52 comparisons must not be described as comparisons against the immediate baseline compiler.
- `build.stdout` records a completed build, and `build.exit` is zero. The current CMake cache says Release with `-O3 -DNDEBUG`. The saved build has warnings, including existing layout signedness and possible-uninitialized warnings outside this change. There is no warning-free-build claim.
- The source manifest, command records, copied executable hash, and release verification agree. This is saved build provenance, not an independently repeated or reproducible build. The earlier compiler's source-to-binary provenance was not independently rebuilt.

Correctness and design assessment

1. One-time evaluation and zero count: `src/wasm_arrays.h:57-130` emits `Gen`, `Convert`, and capture into one local before the zero-count return and before the store loop. The loop reloads that local. It cannot repeat an effectful value expression per element. The frontend replaces accepted constant count expressions with `IntLit` in `src/typecheck_nodes.h:230-259`. C `FreezeFill`, `FixedArrayLitAt`, and `GenArrayLit` use the same capture rule. The fixture's call counter checks positive counts and empty fixed, limited, variable, and grow-only arrays.

2. Scalar and reference repetition: the capture uses the destination element type. `Size`, `StoreFixed`, and `Store` retain the existing scalar width rules. Integers use their packed byte width; booleans use one byte; f32 uses four bytes. Ordinary references retain the captured address. Thin references to fixed arrays have an i32 value but an eight-byte stored slot; the existing store helper extends the value before the eight-byte store. The new loop uses the stored width for its stride. The fixture checks aliasing through scalar references and through repeated fixed-array references, as well as f32 negative zero, bool, u8, i16, and i64 storage.

3. Prefix and allocation arithmetic: variable arrays use `LenStore` and reserve `prefix + count * stride`. The count check precedes the multiplication. Narrow prefixes have a separate range check. Admitted elements have positive fixed size. Unsupported compound and varint layouts fail through the existing type checks before this initializer. Limited inline arrays add their prefix to the base once; the loop's separate prefix is zero for those arrays. `Type` checks the complete static capacity, including the limited prefix. Frame/static storage checks protect the containing address range. `Reserve` adds the old top and byte count in i64, checks the Memory32 end, grows if needed, and publishes the top only after success. Loop bounds then keep the last store within the reserved extent. No input-sized host expansion is needed to prove these bounds.

4. Memory identity and calls: fixed paths use the owner's assigned memory. Dynamic paths capture the identity from the function base and logical owner index, then combine it with the saved low address. The loop preserves the high memory bits. `WasmStoragePlan::Walk` allocates the owner's logical index before it visits the fill expression. `ArrayLit::Children` visits that expression. Calls therefore use a base above the live owner. The O0 fixture calls `large` at different live-owner depths, so it covers a dynamic base and dynamic stores. The O2 fixture covers inlined fixed-memory paths. This is also consistent with the C hidden-stack call convention.

5. Publication and restoration: dynamic arrays reserve the whole payload before value evaluation. They publish the base and count before the expression runs, as the native constructor publishes its count before capture. Local owners record the old top before capture, in the existing ordered cleanup list. Deferred actions and restore actions run in reverse registration order. Globals do not get local restore actions. The reserve helper cannot publish a failed growth. Source inspection supports early-exit restoration during capture, but the new saved fill fixture does not execute such an exit.

6. Later mutation: growable headers contain the packed base and count in the existing 16-byte format. The reserved top is the end of the fill payload, so later push starts after the filled elements. Pop and clear use the same base, width, count, and top rules as before. The fixture checks limited push, grow-only push, and grow-shrink pop after fills. It does not directly check clear followed by push, or repeated shrink/regrow, on a filled owner.

7. Existing paths and scope: only fill literals take the new branch in `InitArray`. Capacity expressions, reusable owners, by-value array results, unsupported elements, strings, and other pending destination paths retain their existing restrictions. The change does not modify C generation, shared layout, memory helpers, storage planning, or mutation code. Reuse of these helpers keeps the fix at the constructor layer. The new reserve/publication code resembles the existing variable initializer; no broader refactor is needed for this extension.

Confirmed defects

None. There is no confirmed valid trigger with an expected/actual mismatch to report. No production fix is proposed. The points below are evidence limits and suggested checks, not confirmed defects.

Saved validation checked independently

All paths in this paragraph are under `/tmp/goose-wasm-array-fills-20261107` unless stated otherwise.

- I read `golden.py`, `golden-results.json`, and `golden-identities.json`. Both original fixture sources equal the promoted frozen fixtures. The prior C backend emitted and ran both at Goose O0 and O2. In this golden stage, the generated C was built with `cc -O0` at both Goose levels. All four native output files equal the frozen expected files.
- The prior Wasm compiler rejected the valid fill fixture at both levels with the exact pending-constructor diagnostic and exit 1. Neither prior fill module exists. This establishes failing-before evidence for the added feature. The cleanup fixture already compiled before the change.
- I read `targeted.py`, its results, and all targeted status, stderr, and output records. Both fixtures at both levels have saved successful emit and validation results. Node, Wasmtime, and owner-check outputs match native output byte for byte. Across the four native and twelve guest/owner outputs, all 16 comparisons match. The targeted scripts use Node 24.22.2 and the recorded Wasmtime Python 49.0.0 environment. I did not rerun either engine.
- The owner checker derives top exports, calls `_start` synchronously, and checks the owners after its return. It asserts frame restoration, all scoped data tops, distinct memory buffers, and the requested growth condition. It does not infer completion from a sleep. For the fill fixture, one persistent global owner is excluded from the scoped-top equality checks. Its exact final top is not asserted; its contents and length are checked through output.
- `wasm.stdout` records 301 checks, with exit zero and empty stderr. I reconciled this count from the frozen harness: 210 helper/fixture/owner checks and 91 later checks. These are harness checks, not 301 distinct programs. I read the full harness, including its rejection and runtime-failure assertions. Individual full-suite command transcripts are not all retained in this stage; this part rests on the saved harness result and artifacts, not a new execution.
- I read `equivalence.py` and independently compared all 68 before/after module pairs, stdout, stderr, exits, sizes, and recorded SHA-256 values. All match. These cover 34 old fixtures at two levels. Both cleanup modules also equal their separately saved prior versions.
- I read `test/backend_shared.py` and checked all 52 compatibility entries: 34 generated C pairs and 18 scalar Wasm pairs. Outputs, stdout, stderr, exits, source hashes, and output hashes match. Native entries compare emitted C and stack reports; they are not 34 additional native executions.
- I read `promote.py`, `validate.py`, `lease.json`, and `release-verification.json`. All seven stage command statuses agree with their exit files. Of 283 saved exit files, only the two expected prior-fill rejections are nonzero. I inspected all 284 stderr files as bytes. Nonempty files are the two expected rejections, the build warnings, and unchanged warning pairs for old fixtures. The saved release record reports reaped children and a released lease; I did not acquire a lease or start work that needs one.
- I read the earlier `constructor-repair02/native.*` records. That native suite exited 1 because it could not locate bundled TinyCC files. It also reports platform and feature skips. I read `constructor-repair03/native-jit-runtime.*` and the relevant rerun command and harness: the exact JIT check passed with `GOOSE_TCCLIB` set to the build's TinyCC directory. This is an earlier suite plus a focused repair check. It is not a fresh full native-suite pass for this candidate. Skipped cases remain skipped.

Footprint and performance

The following values were parsed from saved module bytes with an independent small reader. Local counts exclude parameters and include all defined functions. Every module has ten function imports and one data segment.

| Module | File bytes | Defined functions | Memories / top globals | Total locals | Largest function locals |
| --- | ---: | ---: | ---: | ---: | ---: |
| fills O0 | 12,224 | 28 | 15 / 15 | 358 | 273 |
| fills O2 | 13,377 | 20 | 15 / 15 | 506 | 452 |
| cleanup O0 | 7,923 | 17 | 6 / 6 | 263 | 136 |
| cleanup O2 | 10,789 | 16 | 6 / 6 | 387 | 223 |

The four module hashes match `targeted-results.json`. Fill O2 is 1,153 file bytes larger than O0 and has more declared locals despite fewer functions. This is a file observation, not a runtime regression measurement. No prior fill module exists for a same-input module-size comparison. The saved candidate compiler file is 4,320 bytes larger than the saved immediate prior compiler; this is whole-file size, not a controlled text-section comparison.

For each nonempty fill, the new constructor emits one loop. Its main scratch is four locals for an inline array, or five for a data-memory array, plus bounded scratch from existing header/write/conversion helpers. Empty fills omit the position local and loop, but still evaluate the value. Code and local growth depend on the source expression, type, emitted exits, and helper set, not on `n`. Code buffers, local vectors, cleanup vectors, and helper caches can allocate on the compiler host. There is no new host array or byte buffer of size `n`. First use of dynamic reserve or access can emit dispatch cases for all planned memories; that cost depends on the module memory count, which is limited to 65 including Memory 0.

Guest execution performs `n` stores, so work is O(n), plus one value evaluation. Inline arrays use the existing full-capacity frame/static storage. Variable arrays reserve the prefix plus `n * stride`; growable arrays reserve `n * stride` and retain their existing header. There is one reservation call per data-memory fill, with possible `memory.grow`, and no separate guest heap allocation per repeated element. Repeated references do not allocate or copy their pointees. Dynamic stores call the existing memory-dispatch helper once per element. This can have a cost, but that cost was not measured.

Restoring a data top makes storage reusable. It does not shrink WebAssembly memory or prove that physical pages are released. Engine storage for locals, compiled code, memories, and dispatch is also outside the recorded measurements.

There are no controlled compiler CPU/RSS samples, runtime timing samples, process RSS measurements, or measured allocation counts in the raw data. There is no cross-platform execution evidence. Saved execution is limited to Linux x86-64. Neither a performance gain nor a minimal physical-memory footprint is established. Native, platform, or performance results that are absent are not counted as passed. An optimization decision needs a separate controlled measurement stage; the byte-identical old modules only bound changes to those saved guest artifacts.

Coverage limits and suggested next checks

- The cleanup fixture uses ordinary literals. Add a fill-specific early-return/break/continue case during value evaluation, with surrounding deferred actions and a direct completed-owner top check. First establish native validity and the expected order.
- Reference repetition is checked from stable bindings. Add a side-effectful reference-producing expression, reference rebinding after capture, and an ordinary reference into a data memory. Cover both fixed and dynamic memory stores. No such failure is established here.
- Empty grow-shrink fills, optional/null reference fills, f64 fills, and the full integer-width matrix are not directly exercised by the new fixture. Existing store helpers reduce the changed surface, but their use in these fill combinations remains untested.
- Add a filled-owner clear/push and repeated pop/push case. The current mutation checks cover one append or pop, not all subsequent mutations.
- The Memory32 and narrow-prefix limits are supported by source arithmetic and existing helper tests. This packet has no fill-specific near-limit rejection or forced-growth-failure run. A bounded helper or diagnostic check would be preferable to a multi-gigabyte runtime test.
- The fixture proves growth and completed scoped restoration. It does not establish physical-memory release or the exact persistent global top.

Input coverage and unread material

I read every changed file in full: `src/wasm_arrays.h`, `src/wasm_codegen.h`, `test/wasm_backend.py`, both new `.goose` fixtures, and both expected output files. No changed file is unread.

I also read the full frozen `src/wasm_storage.h`, `src/wasm_memory.h`, `src/wasm_binary.h`, `src/value_layout.h`, `src/data_stacks.h`, `scripts/run_wasm.mjs`, `test/wasm_multimemory.mjs`, and `test/wasmtime_host.py`. Relevant sections of `src/ast.h`, `src/codegen.h`, `src/codegen_construct.h`, `src/codegen_frames.h`, and `src/codegen_calls.h` were read for array representation, capture, construction, calls, and ordered restoration. Their unrelated sections were not read in full.

Supplemental live reads covered fill checking in `src/typecheck_nodes.h`, relevant search matches in `src/typecheck_exprs.h` and `src/typecheck_builtins.h`, array child traversal in `src/clone.h`, the full `test/backend_shared.py`, and relevant build-cache fields. These supplemental source files match both the baseline and the full source manifest. They are not separate frozen packet files.

I read the relevant generated fill-constructor sections in `fills-O0.c`. I did not manually review all embedded runtime code in that file, the other three generated native C files, or the 34 compatibility C outputs. The saved output pairs were compared as bytes. Native executables were hashed, not disassembled or executed. Saved Wasm files were hashed and compared; the four targeted modules also had their section and local counts parsed. I did not manually disassemble every Wasm instruction. The full 4,112-file manifest was hash-checked, not reviewed as source. The full-suite temporary outputs were not each independently audited. Previous review conclusions were deliberately unread.
