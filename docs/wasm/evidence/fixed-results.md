# Fixed nominal call results

Positive fixed structs, enums and variants now return by value through direct
functions, inline bodies and function-value bodies. Each ordinary fixed-result
signature has one private I32 destination parameter after the optional data-stack
base. It has no scalar Wasm result. Nominal values still have no scalar Wasm type.
The callee writes its result image before defers, data-stack restoration and
frame cleanup. Forwarding calls use the same checked destination.

The destination descriptor comes from a real caller owner or a complete checked
Memory 0 temporary. Its span, type, initialization, memory and lifetime are
checked. The incoming callee descriptor is tied to the current function's actual
result and hidden parameter. No synthetic frontend variable or initializer is
used. Results for packed data-memory fields land in a Memory 0 temporary and then
copy into the correct data memory. Assignment also uses a temporary, so argument
effects and callee defers cannot observe an early target commit.

Fixed nominal block and conditional producers use this destination path too.
Each selected branch constructs its result before its scope cleanup. This also
covers declarations, assignments and aggregate arguments that use those producers.
Discarded calls still evaluate their bodies and defers and restore their temporary.
Arrays, named or multiple results, zero-image result transport, nonfixed layouts,
value-producing matches, direct field access on unnamed aggregate results, and
remaining nonlocal boundaries are separate work.

The native-first functional set has twenty-three families at O0 and O2. It covers
direct, inline and callback results, explicit and tail returns, real self-recursion,
early inline returns, forwarding,
global initialization, discard, arguments, enums, defers, block and conditional
producers, data destinations, shallow reference fields, dynamic data-stack bases,
large frame growth, nested returned fields and mixed f32/f64/bool/reference fields.
Both Wasm engines pass all forty-six O0/O2 cases. The old compiler's target failures and the
already-supported optimized inline control are retained. Block/conditional
failures were also reproduced after the first result prototype, before adding
their destination lowering.

The complete packed Memory 0 observer checks argument snapshots, callee local
copies, the returned nine-byte image, defer writes, the permanent target and
restored frame tops. Valid short, long, omitted, wrong-destination, early-target
and missing-restore controls fail specific assertions. A native-first division
failure also proves that a partially constructed return leaves the complete
permanent target image unchanged. An invalid target is rejected before any RHS result-call effect or temporary
reservation. Native-valid empty-result cases retain the
explicit target diagnostic and do not write a partial module.

One early enum fixture used assignment arms without required braces. That
frontend-invalid input remains in the raw records and is not runtime coverage.
Old struct and enum admission helpers expected result calls to fail. Those stale
expectations were reproduced, then changed to execute the now-supported cases.
The first full suite also detected a diagnostic change for aggregate `pop`.
The result dispatch now accepts only ordinary and inline function producers;
aggregate builtins keep their earlier guarded path. The same complete aggregate
admission helper then passed all thirty-six groups. The original failure remains.
No production behavior was weakened to satisfy an admission helper.

A read-only native Codex bug search found no confirmed correctness defect. It
identified early inline returns and callback nonlocal returns as coverage gaps.
Early inline return cases now pass. The first callback probe captured an outer
local and reached that separate guard. A parameter-only native-valid probe then
reached the retained nonlocal-call boundary at both optimization levels; it is a
specific rejection check, not a claimed accepted path. All raw probes remain.
The later builtin-dispatch narrowing was not a second worker review.
The first full-run input list also included generated Python caches. The final
list excludes generated files and is checked independently. The early full run
and its failure remain unchanged; final validation uses the rebuilt compiler.

The ordinary result ABI adds one I32 parameter. Its guest storage and copy work
scale with the complete stored image, as required for independent value results.
The packed-data path needs a Memory 0 landing image and a final cross-memory copy.
Block/inline target descriptors are compiler-local values. No guest heap object
or new runtime descriptor is added. These are source-level cost facts, not
measurements. Joshua's correctness-only directive excludes performance gates,
precision timings and measurement-lease work from this thread.

The final correctness-only Wasm suite passes 2,445 checks, including all forty
complete memory-matrix cases. The final native baseline passes 2,086 frontend,
1,019 generated-C and 1,191 TinyCC groups, plus all other baseline groups.
All 52 exact comparisons pass, and all 530 previous fixture modules are
byte-identical. All 78 source/support files and 4,668 validation inputs match
the frozen hashes. These are checks on the final selected executable, rather
than an earlier prototype's full-suite result.

The selected compiler SHA256 is
`963c3aed896ee678920d69a3cfcee423f65910f114a25b5a5991a73eace618b9`.
Selected records and their raw hashes are in the
[archive manifest](fixed-results/archive-manifest.json). The separately named
prototype identity is historical. Raw binaries, generated modules and complete
records remain in `/tmp/goose-wasm-fixed-results-20261108`.
Linux native execution and the configured Node/Wasmtime hosts are the execution
coverage. No performance, allocation, or cross-platform runtime claim is made.
The complete backend remains unfinished.
