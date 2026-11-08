# Fixed aggregate call arguments

Positive fixed structs, enums and variants now work as by-value arguments to
ordinary functions, inline bodies and function-value bodies. Ordinary calls
use private Memory 0 snapshot addresses as I32 parameter transport. Nominal
values do not become scalar Wasm values. The callee copies each incoming image
into its own checked frame slot before its body runs. Native extern/export and
worker guards remain unchanged.

The caller snapshots each fixed argument at its evaluation point, before later
arguments can change its source. Scalar and reference arguments in these mixed
calls are saved at the same point. A scalar/reference result is saved before
argument snapshots are restored. Inline and function-value bodies construct
values in the real planned parameter owners before evaluating later arguments.
Their plans use actual VarDefs, VarDecls, calls and function specializations.
No fake frontend variable or initializer is used. Zero-image variant parameters
remain explicitly guarded in this first argument step.

Parameters are independent value copies. They can be changed without changing
the source or another parameter copied from the same source. Reference fields
remain shallow: the copied reference still reaches the original pointee.
Frontend lifetime and return-root checks remain the authority. A caller with no
static frame and a global initializer use checked temporary reservations, with
ordered restoration, rather than an uninitialized frame-base local.

The checked native-first set contains fifty-two O0/O2 cases in twenty-six source
families. It covers direct, inline, callback and repeated callback calls,
left-to-right ordering in all three paths, reverse mixed ordering, recursion,
global initialization, void and reference results, callee defers, later-argument
return, fixed/limited array fields, data sources, large images and dynamic data
stack bases. Both Wasm engines pass these functional cases. Final module equivalence and
supplemental checks below tie them to the selected compiler. A native-invalid always-return argument attempts to pass void as i64;
it is retained as invalid input and is not coverage of that runtime path.

A copied full Memory 0 model checks one packed nine-byte snapshot, its separate
callee image, defer writes and caller completion. Valid short, long, omitted,
original-source and missing-restore mutations fail their named assertions.
A second validated control aliases two callee parameter slots and fails the
distinct-address assertion. The dynamic-base observer checks both real data
stack tops and payloads at two caller depths, then checks restoration after
completion. Its validated wrong-base control fails the named namespace check.
Empty parameter and frame-overflow guards are tested with native-valid inputs;
the huge case is C-emission-only and is never built or executed.

The implementation adds one function-owner pointer to each compiler-side fixed
owner record. A mixed ordinary call uses a capture vector and recursive emission
continuations proportional to argument count. Snapshot and parameter-copy work
is proportional to the complete stored images. The snapshots preserve value
isolation and source order; the callee images retain the ordinary frame-owner
contract. This adds no guest heap object or runtime descriptor. A planner
refinement reuses the existing argument walk's count instead of allocating a
second argument vector. Callback owner lookup uses the checked parameter
index instead of scanning the parameter list for each argument. These are
source-level costs and reasons, not runtime,
compiler-allocation or physical-memory measurements.

## Preserved failures and limits

The first focused helper wrongly marked a data-backed reference case as Memory
0 only. Its native, Node and Wasmtime values had passed; the mode assertion was
the failure. The continuation hash-verifies completed cases and runs only the
unfinished checks. A later dynamic observer assumed a zero data-stack base.
The saved module and existing owner tests prove that the initial top is one.
The corrected observer reads those real tops, with the failed observer retained.
All fifty earlier functional cases and completed controls are preserved.
The later mixed-scalar family also checks f32/f64 arguments, float and bool
results, and reference writes.

The old struct admission table expected argument calls to fail; that failure
was reproduced before promoting those inputs to accepted behavior. The enum
argument inputs still contain a value-producing match. They now stop at that
separate guard, while positive enum argument cases use statement matches.
A full native run found two missing warning markers for redundant reference
operators. Only comments were added, with all four affected modules proved
byte-identical and rechecked in both engines. The original failed native run
and the original source hashes remain separate.

General aggregate results, by-value arrays, nonfixed stored fields, stored
references to growable owner headers, zero-image parameters, layout adaptation,
remaining nonlocal call boundaries and native/WASI/worker adapters remain
separate compilation work. This does not complete the backend.

The complete 2,279-group Wasm run passes, including all forty complete memory
matrix cases. The later indexed-owner API refinement regenerates all 528
fixture modules byte-identically and repeats all 24 private control groups.
The two warning-only fixtures have four identical recompiled modules and both
engine rechecks. The added mixed-scalar family passes O0/O2 in both engines
and the completed-owner checker. This is reuse of identical guest-code evidence,
not a second claimed full 2,279-group execution on the later executable.

The final native baseline passes 2,040 frontend, 996 generated-C and 1,168 TinyCC
groups, plus all other baseline groups. All 52 exact comparisons pass; 478
unchanged parent module pairs are identical. All 73 source hashes and 4,620
final validation input hashes match. The selected compiler SHA256 is
`4cf1b2d137582fd664f91d8bec99983514860d60d91a28851d2629b9935b01b0`.
Selected records are in the [archive manifest](fixed-arguments/archive-manifest.json).
The archived ABI design predates this implementation and includes later result
work; it is not a code review or evidence that those later stages are complete.
Raw evidence remains under /tmp/goose-wasm-fixed-arguments-20261107. No timing,
measurement lease or performance acceptance gate is used.
