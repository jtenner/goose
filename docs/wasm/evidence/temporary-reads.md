# Scoped reads from fixed temporaries

The Wasm backend now reads scalar fields, indexed elements, array length and
capacity from fixed stored producers. These include direct, inline and callback
results, literals, defaults, copies, blocks and conditionals. Nested projections
can also copy a complete fixed field or element into a checked destination.
The temporary remains live while field selection and effectful indexing run.
The selected scalar or contained-reference value is saved before cleanup.

This uses the existing checked Memory 0 temporary owner and ordered cleanup.
There is no new runtime descriptor, compiler field, IR node or heap callback.
The recursive compiler callback uses stack contexts and one erased callback
type. Stable owners retain their existing emission path. Stored reference
values keep their target identity, including packed data-memory addresses.
Field/index reference identity and null tests use the same scoped read.
Taking a reference to storage inside the temporary is still rejected. The
current implicit field and element borrow paths retain their exact existing
target diagnostics and leave no partial module.

## Correctness evidence

The twenty-four native-first positive families cover O0 and O2: direct, inline
and callback roots; global reads; literal/default/copy/block/conditional roots;
fixed and limited arrays; scalar bool/f32/f64 and signed zero; contained-reference
identity and null tests; nested reference projections; complete aggregate field
copies and assignments; single evaluation; effectful indices; and return,
break and continue inside an index. Both Node and Wasmtime pass all forty-eight
case/optimization pairs. Completed-owner and restored-top checks also pass.

A complete Memory 0 model checks the returned array and the index function's
scratch array while both are live. It checks all bytes, sentinel bytes, the
index mutation, restored tops and the final image after guest completion.
The index uses a separate reference call, so its scratch owner stays required.
Valid early-release, missing-restore and wrong-image modules fail the named
live-top or full-image assertion. Eight healthy/control image checks and four
native-valid address-guard checks pass.

A read-only native Codex bug search found a reference-comparison compilation
gap in the first prototype. Native-valid identity and optional-null cases
reproduced the exact target rejection before the narrow ReferenceValue dispatch
fix. They now pass in both engines. The audit found no confirmed wrong-result
or lifetime defect in the scoped projection/copy path. It also requested
loop-exit and nested-reference cases, which are included above.

## Preserved failures and limits

The first prototype build failed because a callback called TEq without its
WasmCodeGen receiver. Its compiler error is retained. A later focused run had
eleven passes and three pending constructor/copy roots, despite its copied
summary claiming fourteen passes. The raw summary and corrected scope record
are both retained. The final compiler accepts those roots.

The first live-owner native check returned all three correct checkpoint lines;
its copied driver expected one line. Completed results were reused after the
driver correction. The final focused run passed all forty-eight positive pairs
and eight image checks, then stopped on an overly specific address-guard
expectation. A second guard helper exposed the separate array-address diagnostic.
The final helper requires the actual exact field and element reasons. These
were test-driver errors. No production change was made to accept the borrows.
The first full suite then found an obsolete admission check that still expected a literal field read to fail. That check now requires output1 in both engines. The same compiler is used for the corrected full run. Raw failures, commands, stderr and exits remain separate.

Live temporary bytes and copy work grow with each complete stored image and
active expression depth. Scalar capture adds a Wasm local. Projection traversal
on the compiler stack grows with source path depth. These facts do not measure
runtime, compiler allocation, RSS or physical memory. No performance run,
measurement lease or performance gate is part of this correctness-only work.
General aggregate comparisons, references escaping temporary storage, nonfixed
results and remaining compound lifetimes are separate compilation work.

The final correctness-only suite passes 2,989 Wasm checks, including all forty
complete memory matrix cases. The native baseline passes 2,246 frontend,
1,099 generated-C and 1,271 TinyCC groups, plus every other baseline group.
All 52 exact comparisons pass. All 688 unchanged parent fixture modules are
byte-identical. All 78 compiler/support and 4,835 final validation-input hashes
match the tested executable and source. The first full-run failure is retained;
the corrected complete run uses the same compiler.

The selected compiler SHA256 is
`7df8dad28b11cc4a37367bd0ec7c9a5ed880bb773625388fa1c2d8150569b8ac`.
Selected records and their raw hashes are in the
[archive manifest](temporary-reads/archive-manifest.json). Raw binaries and
complete producer records remain in
`/tmp/goose-wasm-fixed-temporary-reads-20261108`.
Execution evidence is Linux native and the configured Node/Wasmtime hosts.
The full backend is not complete.
