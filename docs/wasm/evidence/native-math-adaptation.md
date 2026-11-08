# Native aggregate arithmetic at adapted destinations

A native-first probe for Wasm negation found a separate C backend error.
Arithmetic on a two-element fixed array, received as a larger limited array,
used the receiving capacity as its arithmetic bound. Saved C read beyond the
source and did not set the receiving length. Both unary minus and binary
arithmetic failed. Variable and growing receivers could instead crash the
compiler during C emission. These are valid checked inputs. All 47 focused sources pass the saved parent frontend without C emission.

The C emitter now uses the aggregate operand type while it emits arithmetic.
A scoped override restores the checked receiving type, including on an emission
error. Fixed C values then pass through the existing receiving-layout adapter.
Data-stack construction keeps the receiver type in its destination descriptor.
Direct member writes require matching source-result and destination layouts.
Nested constructors use the same rule. The adapter copies the source count and
sets the receiving length; arithmetic does not run over unused capacity.

The source type lookup is bounded by the two operands. The scope has no heap
allocation or persistent compiler field. Matching-layout arithmetic keeps its
existing alias and operand-order logic. Adapted payload copies are required to
construct the destination layout. No runtime service or Wasm ABI changed.
No performance measurement was run under the correctness-only owner directive.

## Failing-first and focused checks

The first four saved O0/O2 native runs compiled but failed their exact length
assertions. The expanded parent matrix has 27 assertion failures, 16 C-emission
crashes for variable/growing receivers, and one healthy exact-layout alias case.
All 44 cases pass with the candidate.

Three permanent fixtures cover all arithmetic operators, both scalar-broadcast
directions, equal/larger limited capacities, variable/growing arrays,
assignment, returns, arguments, nested fields/elements, exact-layout aliases,
F32/F64 and narrow integers. Additional cases cover later operand mutation,
recursion, callbacks, nested arrays/structs, a 600-element result, and a
runtime-capacity receiver. The failure fixture requires the capacity diagnostic
and exact output before failure. It does not inspect destination bytes after
the process aborts.

The permanent fixtures crash the saved parent during C emission. All twelve
candidate GCC/Clang O0/O2 builds and executions pass, including undefined-behavior
sanitizer runs and the required capacity failure. The original diagnostic attempt
against parent generated C did not report the expected bounds error. It reached
the existing runtime assertion instead. Its failed helper and raw output remain
preserved; it is not counted as a successful sanitizer reproduction.

A separate read-only native Codex bug search found no confirmed defect in the
fix. No worker builds or tests were run.

## Backend limit

This is a native correctness repair. Wasm still rejects layout-changing fixed
negation at its exact-layout guard. It emits no partial module. General binary
aggregate arithmetic and other compound adaptations remain pending.

Full-suite and frozen-identity results are recorded in the adjacent archive.

The complete native baseline passes all 18 groups, including 2,364 frontend,
1,158 generated-C and 1,333 TinyCC checks. The 52 exact native-output and
diagnostic comparisons also pass.

Raw evidence is retained at `/tmp/goose-native-math-adaptation-20261108`.
The [archive manifest](native-math-adaptation/archive-manifest.json) records
the selected compiler, frozen source hashes, commands, failing-first records,
controls and check results. Generated C examples are compressed without changing
their contents.

The full Wasm correctness suite passes all 3,359 checks. All 848 prior fixture
modules match byte for byte using the completed suite outputs, without a guest
rerun. All 78 compiler source files and 4,960 validation inputs match the frozen
manifests after validation. The tested executable hash is recorded in the archive.
Execution evidence is from Linux; no cross-platform execution claim is made.
