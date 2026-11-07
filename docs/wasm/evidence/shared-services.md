# Shared stack and layout services

This change prepares the direct Wasm backend for data-stack assignment and
compound values. It does not complete stage C or add a new Goose value class.

`DataStackCounts` contains the existing C backend's call-bound calculation.
The C emitter still records lexical allocation counts and call watermarks.
The shared graph service checks recursive edges and computes each component's
bound. `ValueLayout` contains the concrete-type, numeric field-layout, count,
tag, reference-width, and resizable-tail byte-prefix queries previously owned
by `CodeGen`. Both backends use that authority. C naming, declarations, and
emitted header-size expressions remain in the C emitter.

Validation used a Release rebuild whose compiler SHA256 is
`c30a6d3ebd9890579c7ec854db3d018a12eca35666511e75cfa5f263b133f67f`.
The preserved scalar-checkpoint compiler SHA256 is
`858f4092702b85300103afb4427b4d0f2a8be3701c7d0e83a8d91f1b2a3a0de6`.
Both exact binaries and the full generated comparison artifacts remain in the
raw evidence directory recorded in the source manifest.

- The graph unit checks overlapping owner lifetimes, released-scope reuse,
  recursive components with external callees, self recursion, global work,
  and the exact invalid recursive edge and location.
- Seventeen existing native fixtures and nine scalar Wasm fixtures at O0/O2
  give 52 exact generated-output and diagnostic comparisons. Every generated
  C file, stack report, Wasm module, exit, and diagnostic matches the preserved
  compiler.
- The full native baseline suite and 94 Wasm checks pass. The Wasm suite uses
  wasm-tools, Node, and Wasmtime, with separate native-output comparisons.
- The graph unit is registered in the native runner's existing C++ unit hook.
  A subsequent full native-suite run passes with that registration.
- Astra independently reviewed all 11 core files and all 52 saved comparisons.
  It reported no confirmed defects. The one-line test registration was added
  after that review and checked by the normal native suite.

Generated-program runtime paths and output sizes are byte-identical for the
comparison fixtures. The C service retains its existing maps, cache, and graph
traversal. Wasm gains an empty layout cache and repeats scalar type validation
before its size query. Compiler time, executable size, and allocations were
not measured, so no compiler-cost gain is claimed. Native execution evidence
is Linux x86-64 only. Existing device, platform, and unsupported-JIT skips
remain in the logs.

Two bounded lock turns covered the build/validation and test registration.
Both released the shared lock after all owned children were reaped. No
performance samples were taken. Source work continues while the other owner
uses its lock turn.

[Source and compiler identities](shared-services/source-manifest.json),
[exact comparisons](shared-services/equivalence.json),
[independent review](shared-services/astra-review.md), and raw stdout, stderr,
exits, and lease records are preserved in [the evidence directory](shared-services).
