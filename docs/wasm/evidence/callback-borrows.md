# Fixed temporary borrows through callback bodies

Parent: ca3e6f45388abdbe483d200552c7b18d6c8fd4b1.
Branch: `feat/wasm-multimemory-backend`. Scope: Stage C correctness only.

Function-value callbacks with a scalar or void result can now borrow fields and
elements of fixed temporaries. Argument binding keeps each owner live through
later arguments and the callback body. The scalar result is saved before the
ordered owner restore. Fixed value parameters still use the existing planned
frame owners. The normal binder shares its existing argument vector with the
call emitter instead of creating a second vector.

All 22 admitted families are native-valid. Their 44 O0/O2 variants fail Wasm
compilation on the parent. The final compiler passes 44 fresh native, Node and
Wasmtime pairs. Cases include packed numeric fields, aggregate and array
subobjects, multiple owners, mixed value arguments, data memories, growth,
void calls and later return/continue/break paths. The exit targets are inside
the apply function; invalid callback exits into a caller loop are not counted.

Complete Memory 0 models and specific damaged-module controls pass 16 checks.
They detect owner release before a later argument or body, missing final
cleanup, wrong values, and outside-owner writes, including after memory growth.
Four native-valid optional-reference-result cases remain rejected for the exact
pending-lifetime reason. Their results can outlive the current owner scope.

An early uncommitted result gate used the callback's empty result list. The
frontend records the inferred result on the checked body. A source bug search
found the mismatch. Before changing the gate, a same-statement optional-reference
case passed native execution and failed a Wasm assertion after a later argument
call. The final gate reads the body type and excludes reference results. The
wrong-result module, compiler, source hashes and outputs remain in the raw
records. This defect was in the uncommitted increment; the parent rejected the
temporary borrow. The worker performed source reads only.

The final suite passes 8,260 checks. Core and every suffix helper run fresh.
The 2,138 executed fixture records comprise 2,094 parent modules with exact
source and candidate-byte identity and the 44 fresh pairs. All 52 exact output
and diagnostic comparisons pass. The tested compiler SHA256 is
`576b8ea5fb611013d9b5105c1c2b63b3d8039cd3d43c2980e99cbcf29b1b6aef`.
All 85 source and 6,225 test/script input hashes match the frozen records.

Other retained setups include invalid plain-reference guard sketches and image
parser assumptions about the function that owns the temporary. O0 keeps that
owner in `apply`; O2 moves it into `main`. The corrected helper inspects the
emitted listing. No compiler rebuild or guest behavior change was needed for
the image-parser corrections. Failed attempts remain separate.

No runtime field or public ABI changes. Newly supported expressions use the
existing checked temporary reservation/copy and restore. Compiler work grows
with the checked arguments and selection paths; continuation depth follows the
borrowed owners. No extra argument vector or new heap service is added. These
are source-level cost limits. No measurements, timing, profiling, allocation
or physical-memory claims are part of this checkpoint.

The backend is not complete. Remaining Stage C work includes other inline
bindings, nonfixed owners, compound lifetime events and general thin-reference
and reference-result propagation. Stages D, E and F follow in order. Stage F
is in scope. See the [raw archive manifest](callback-borrows/archive-manifest.json)
for commands, outputs, failures, hashes and source snapshots.
