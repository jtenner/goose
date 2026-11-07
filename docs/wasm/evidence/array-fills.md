# Scalar and reference fill constructors

This stage adds `[v; n]` to the admitted fixed, static-capacity limited,
fixed-prefix variable, grow-only and grow-shrink array layouts. The unchanged
frontend checks the nonnegative constant count. The emitter evaluates and
captures `v` once, including for a zero count, then stores that value or
reference target in a loop. Compound elements, varints, strings, runtime
capacities and general value destinations remain pending.

Data-memory fills make one checked whole-payload reservation. The packed
prefix and element widths come from the existing shared layout service.
Scoped owners enter the existing ordered cleanup list before the value runs;
calls in the value use stack bases above that owner. Inline fills use the
checked Memory0 activation or global region. Loop bounds and the checked
reserved range prevent offset wrap. Known memories use direct stores; dynamic
bases use the existing checked dispatch. Constructor bookkeeping is independent
of the fill count. Runtime stores still grow with that count.

The native-valid test inputs first ran through preserved compiler SHA256
`ccb45b63e07c3dc3a80ef392e12db035453b6fd65cd7e7b4387efb5222ad464f`.
Their O0/O2 output matches. The prior Wasm path rejects the fill fixture at the
specific unsupported-constructor diagnostic and writes no module. The direct
variable-owner cleanup fixture already works before this extension.

The new Release compiler SHA256 is
`668f2d0c863823789a1b6fc04dac145e49996602fc79641950ea69f0cb570ffb`.
Targeted O0/O2 output matches native in Node 24.22.2 and Wasmtime Python 49.0.0;
wasm-tools 1.262.0 validation and post-completion owner checks pass. Cases include
zero-count effects, mutable scalar reference targets, thin array-reference
payloads, global data, signed zero, narrow elements, later push/pop, successful
growth, and a 9,000-element fill called at different live-owner depths. The
ported cleanup case directly checks variable owners with defer, return, break
and continue. Owner state is read after synchronous `_start` completion.

The full Wasm suite passed 301 checks. All 52 exact C/scalar-Wasm/stack-report/
diagnostic comparisons passed, and all 68 prior Wasm modules remain byte
identical. The prior checkpoint's full native run plus its exact packaging
setup correction remains the full native baseline evidence; this stage ran
new native oracles and exact native comparisons, not another full baseline.
The saved source manifest matches the tested compiler source. All resource
children exited and were reaped; owner 3371582 exited; the lease was released
and a fresh nonblocking exclusive probe passed and was immediately released.
Raw evidence is preserved at `/tmp/goose-wasm-array-fills-20261107`.

The combined fill module is 12,224 bytes at O0 and 13,377 bytes at O2. Its
maximum function-local counts are 273 and 452, respectively; these totals
include all constructors, calls and optimizer inlining in that fixture. They
do not isolate per-constructor runtime memory. The cleanup modules are 7,923
and 10,789 bytes. No compiler CPU/RSS, host allocation counts, guest runtime
samples or process physical-memory measurements were taken. A restored stack
top does not shrink Wasm linear-memory capacity. Native/Wasmtime/Node runtime
comparisons and compiler-cost measurements remain in the project's later
coordinated performance matrix. No general speed or memory gain is claimed.

An independent Astra review found no confirmed correctness or design defect.
Its [report](array-fills/astra-review.md) verifies the saved identities and
comparisons and lists remaining coverage gaps. Fill-specific capture exits,
side-effectful reference-producing values, the full scalar-width matrix and
near-limit growth failures remain limits, not verified defects. The exact
[release record](array-fills/release-verification.json), raw statuses, source
hashes and comparison summaries are retained beside that report.
