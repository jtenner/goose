Independent review of the Goose shared services extraction

Confirmed findings: none. I found no valid input or reachable call graph that shows a correctness regression caused by this patch. The design is suitable for the stated extraction stage. This assessment does not establish compound Wasm or multi-memory support.

I performed this review myself. I did not use subagents or Claude. I did not run a compiler, build, test, benchmark, timer, or resource job. I read source and existing evidence, compared saved files, and checked hashes. This report is my only file change.

**Reviewed identity**

- Baseline: `113dc3ae7b75d4258764135b3c94413c0465641c`. The stated upstream base is `7b90f91d91845f4ef1712e16ed053f395e4e6e1c`.
- Candidate: frozen uncommitted patch SHA256 `a7f3190a766a64c9e47b0f5452bc947abf0d242eb0d880c8925cf5ae8b9b19da`.
- Candidate compiler SHA256: `c30a6d3ebd9890579c7ec854db3d018a12eca35666511e75cfa5f263b133f67f`.
- Reference compiler SHA256: `858f4092702b85300103afb4427b4d0f2a8be3701c7d0e83a8d91f1b2a3a0de6`.

I read `manifest.json` and all of `change.patch`. All 11 candidate hashes match the manifest. The seven preserved baseline files match their files at the baseline commit. I reconstructed each candidate file from the patch in memory and compared it with the packet. All 11 matched. The checkout HEAD is the baseline commit. Its scoped source files and both compiler binaries also match the packet identities at review time. These checks support the recorded build identity; I did not rebuild either binary.

**File coverage**

I read every candidate file in full. Line numbers below refer to the frozen candidate.

| File | Review coverage and result |
| --- | --- |
| `CMakeLists.txt` | Both headers are listed. C++20 and platform build settings remain unchanged. |
| `src/main.cpp` | The services follow the AST definitions and precede both backends. Each generator remains local to one compile and is destroyed before its AST. |
| `src/codegen.h` | Checked inheritance, inherited queries, constructor use, cache lifetime, lexical call recording, and all remaining declarations. The three accounting maps move into one owned service. |
| `src/codegen_types.h` | Checked all remaining type emission, serialization, equality, and prefix callers. The C-specific operations remain in CodeGen. |
| `src/codegen_stacks.h` | Checked the diagnostic adapter, root selection, stack limits, worker counts, and reports. They consume the same bounds. |
| `src/codegen_emit.h` | Checked body reset, element-run twins, global initialization, and final reservation emission. Own-stack counts still use the maximum across emitted forms. |
| `src/wasm_codegen.h` | Checked all size callers and the scalar type gate. Accepted stored widths remain unchanged. |
| `src/data_stacks.h` | Checked the complete graph traversal, component reduction, null root, and invalid-cycle callback. |
| `src/value_layout.h` | Checked every query, numeric rule, field walk, cache key, and cache insertion. |
| `test/data_stacks.cpp` | Checked each graph and assertion, including exact caller, callee, offset, and location for the rejected cycle. |
| `test/backend_shared.py` | Checked fixture selection, compiler arguments, captured diagnostics and exits, byte comparisons, and identity records. |

I also read the relevant preserved baseline declarations and implementations. Supporting checkout reads included `includes.h`, AST storage and field-run definitions, the frame-object checks in `typecheck_types.h`, direct and dispatch call recording in `codegen_calls.h`, format call recording in `codegen_render.h`, and frame-to-byte conversion in `codegen_construct.h`. I inspected the unit-test registration in `test/run_tests.py`, all of `test/wasm_backend.py`, and selected layout and Wasm frame fixtures.

**Correctness and design assessment**

At `src/data_stacks.h:30`, Bound preserves the baseline Tarjan traversal. It visits reachable callees even when the caller supplies only entry roots. It also visits the null function used for global work. Each recursive component receives the maximum of its own counts and its outgoing call offsets plus the final callee bounds. Internal cycle edges must have zero offset. The adapter at `src/codegen_stacks.h:22` still throws the same diagnostic with the original edge location and function names.

The actual C call sites still record `stknext` immediately before they pass `SpTop()`. This holds for direct calls, dispatch calls, and user format calls. The extraction does not replace lexical offsets with whole-function maxima. ResetFnState leaves the accumulated service records intact. EmitProgramInit computes the final bound after normal bodies, global initialization, element-run twins, and render helpers have been emitted.

The 14 out-of-class methods moved from CodeGen to ValueLayout have identical bodies after whitespace normalization. I also compared the moved inline queries and declarations. The extraction preserves these rules:

- Explicit padding contributes its declared width. Bare padding aligns the next real field in fixed layouts.
- Empty structs retain one byte. Empty variant payloads retain zero packed payload bytes.
- Static limited-array count widths retain the 255, 65535, and UINT32_MAX boundaries. Variable-array default count storage remains u32.
- Tags retain the one-byte/two-byte boundary at 256 variants.
- Ordinary references retain eight stored bytes, resizable references retain 16, and relative references retain their declared width. Slices retain 16 bytes.
- FoBytesPrefix adds fixed fields and explicit pads through nested frame-object tails. It does not insert bare-pad alignment into that byte image. This remains distinct from C frame-header size calculations.

At `src/wasm_codegen.h:61`, Size now calls Type before FixedSize. Type still rejects compound values, relative references, varints, and index/bound types. Thus the wider shared query does not admit unsupported Wasm layouts. Accepted references still occupy eight bytes in packed memory while their Wasm address value uses i32. The new memory32 range check does not change accepted scalar sizes.

ValueLayout owns its numeric layout map. Its keys are AST-owned struct/enum instances and variant indices. Each backend has its own cache, with no process-wide state. The AST outlives the service. Map insertion preserves references to existing cached layouts. SI and EIOf still fill existing TypeExpr instance-pointer caches on a fallback lookup; the service is therefore not strictly immutable despite its opening comment. It creates no new type instantiations. The current single-threaded, post-check use is consistent with that contract.

The shared layer does not call C emission, naming, or TypeCheck. Public nonvirtual inheritance adds no virtual dispatch. ValueLayout follows the existing project header-order convention and requires the common includes and complete AST definitions first. DataStackCounts includes its own standard-library dependencies and does not require Goose AST types. I found no new platform-specific API or native pointer-size calculation in either service. Source inspection supports the existing Windows, Linux, and macOS build model; execution evidence is limited as stated below.

**Compiler operation and allocation costs**

The C graph pass retains expected O(V + E) traversal work with hash containers. Its stored graph uses O(V + E) space. Traversal maps, sets, component vectors, and recursive std::function storage remain compiler-owned costs. The template does not copy the graph or the supplied root vector. It passes the invalid-edge callback by value; the current callback captures only the generator pointer. Exact callable allocation and generated compiler code size were not measured.

The C layout cache retains one map entry and offset vector per requested struct or variant layout. Cache lookup remains logarithmic in the number of cached layouts. Existing work that depends on type structure also remains: instance fallback searches, variant maximum scans, recursive size queries, and look-ahead across bare padding. A long run of bare pads can cause quadratic scanning in LayoutFields. This behavior already exists in the baseline; the extraction does not add it.

WasmCodeGen gains an empty layout-map member. Its accepted scalar queries do not populate that map. Size also repeats Type validation that its current callers already perform, then calls FixedSize and checks the range. This is extra compiler work. For reference types, Type follows the pointee chain. There is no new per-query container allocation on the accepted scalar path. Empty-container construction costs depend on the C++ library, so I do not claim zero additional compiler allocation on all platforms.

No new generated-program state or allocation is apparent in the changed code. The saved C and Wasm artifacts are byte-identical for all comparison fixtures. This supports unchanged runtime work and output size for those fixtures. It does not establish a compiler-time, compiler-allocation, executable-size, or general runtime performance gain.

**Recorded evidence inspected**

I read all stdout, stderr, and exit files for `build`, `stack-unit-build`, `stack-unit`, `equivalence`, `native`, and `wasm`. All six recorded exits are zero. I read `validate.py` and `lease.json`; the lease records completion, reaped children, and release.

I read `equivalence/summary.json` and independently compared all 416 paired artifact files. All 52 comparisons match generated C/Wasm bytes, stdout, stderr, and successful exit status. Their output hashes match the summary. All fixture hashes match the checkout. The set contains 17 native and nine Wasm fixtures, each at O0 and O2. Both compiler hashes in the summary match the manifest and the binaries on disk.

The native baseline-profile log reports all executed tests passed. It includes 740 generated-C checks, 210 debug checks, 912 JIT checks, and the recorded parser, typechecker, driver, runtime, and bootstrap groups. It also records skips for unavailable graphics/audio/UI features, unsupported JIT cases, huge pages, and the Windows commit-limit check. The build did not include gfx. Build stderr contains warnings, but no failure; I found no new shared-service warning in it.

The Wasm log reports 94 checks passed. The recorded command enabled both Node and the optional Wasmtime host. The harness includes native-output comparisons, module validation, frame growth, runtime failure checks, and unsupported-feature diagnostics. Its binary encoder tests do not establish compound or multi-memory Goose lowering.

**Unverified risks and coverage limits**

There are no confirmed defects to assign a severity, triggering input, or required fix. The following items remain limits or optional follow-up work:

- Compiler cost changes are unmeasured. If a later stage claims lower compile time or memory use, measure both against the identified baseline with a fixed workload. The extra Wasm cache member and repeated type checks should be included.
- The new graph unit is not registered in the standard native runner or CMake tests. The packet proves a separate invocation, with assertions enabled by the recorded command. Register it in the normal runner if continuous coverage is intended. It covers four useful graphs, but is not an exhaustive graph check.
- Numeric-layout coverage is indirect through existing fixtures and exact compiler-output comparisons. Dedicated ValueLayout tests for width boundaries, nested frame tails, cache hits, and instance-cache fallback would improve isolation before compound Wasm use. No such direct unit test is present in this patch.
- Future service callers must preserve the checked-type and cache-lifetime contracts. An invalid-cycle callback must throw or ensure that its reported bound is discarded. The current C adapter throws. The present review does not prove safety for future concurrent access, changing checked layouts, or new ABI policies.

Native execution evidence is only from Linux x86-64. There is no candidate Windows, macOS, or native ARM execution evidence in this packet. No compiler timing or allocation measurements were taken. I did not run fresh validation or mutation tests, and did not demonstrate tests failing on deliberately broken code.

Unread material: no candidate file, patch section, manifest entry, or requested saved text evidence remains unread. All paired output artifacts were read and compared as bytes; I did not manually audit every generated C line or disassemble the Wasm modules. I did not disassemble the compiler binaries or the saved `data-stacks` executable. Unchanged source outside the supporting sections named above was not fully audited. The broader native and Wasm runs provide summary logs rather than a complete per-subprocess evidence archive in this packet.
