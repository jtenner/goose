# Scalar review and regression evidence

Two independent read-only workers reviewed the implementation: GPT-6.1-Sol
for scalar lowering and GPT-6-Astra for design and correctness. No Claude
review was used. The reviews inspected all changed implementation and test
files. The Astra report records its exact executable identity and the driver
change that required a later rebuild. Neither review is a benchmark or an
approval of the complete multi-memory project.

Confirmed cases were reproduced before correction:

| Case | Before correction | Permanent check |
| --- | --- | --- |
| Implicit/widened function tails | Compiler exited 0; wasm-tools rejected leftover values | wasm_tail_values.goose, O0/O2 |
| Optional RHS of logical operators | Native `true`; valid Wasm `false` in comparison with `true` | wasm_tail_values.goose |
| Optional printing | Compiler exited 0; validator expected i64 but found i32 | wasm_tail_values.goose |
| Abandoned print argument | Ten host buffers remained at the final output signal | wasm_runtime.mjs checks the owner's pending count at print completion |
| Output `%` expansion | Source file replaced with Wasm bytes | wasm_backend.py checks source bytes and the per-file failure marker |
| Reference-return decay | Valid native program; target rejected scalar conversion | wasm_reference_returns.goose |
| Float reference identity | Float comparison opcode received i32 addresses | wasm_reference_identity.goose |
| Narrowed optional null test | Nonnull bool reference to false compared as null; integer/float modules invalid | wasm_reference_identity.goose |
| Scalar reference rebinding | Valid native program; target entered arithmetic lowering | wasm_reference_rebind.goose |
| Static span above Memory32 | Attempted allocation, caught as bad_alloc under bounded address space | wasm_binary.cpp valid lazy span with limited process address space |
| Unsigned module field above u32 | Encoder accepted an invalid field | wasm_binary.cpp checks rejection and exact multi-byte memargs |

The parent checked findings against source and subprocess results before
correction. New tests compare separately compiled native C and Wasm under
Node, with optional Wasmtime execution. They assert specific failure reasons,
not only a nonzero status. The full native suite is also required after the
source freeze. Unsupported later-stage operations remain explicit diagnostics.

Memory behavior: scalar numeric execution uses Wasm locals, and address-taken
scalars use checked Memory 0 frames. Print uses O(argument count) scalar snapshot
locals to preserve values before later argument effects, then one buffered host
line. The initial wrapping float-to-int adapter uses a host BigInt operation;
that call/conversion cost is not optimized away. The benchmark conversion
workload exposes this cost. No measured speedup is claimed.
