# Fixed array values into nonfixed array owners

The Wasm backend now constructs variable, grow-only, grow/shrink,
runtime-limited and unsigned-LEB-prefixed array owners from fixed array values.
Stored values, reference-returning calls, fixed call results, defaults and fixed
numeric expressions use the receiver's existing storage plan. Direct literals
retain their existing construction path. Source and receiver element layouts
must match.

Computed fixed values use one checked temporary in Memory 0, then copy the
payload into the receiver. Stored values use the existing read-place path.
The receiver stores its own length or capacity/length prefix. Growable receivers
keep their Memory 0 header. The allocator uses the receiver's planned memory;
cleanup belongs to the declaration scope, not to the shorter expression scope.
Global owners retain their data. No new persistent compiler table or allocator
is added.

A narrow scalar-emitter guard now accepts the actual reference result type of a
call or inline call when the consumer explicitly asks for that reference type.
This permits the read-place service to use a fixed reference after the frontend
has adapted the expression type to the nonfixed receiver. Indexed values retain
their original guard.

## Correctness evidence

Forty-five native-valid families fail to compile on the parent Wasm backend.
The candidate passes all 90 O0/O2 native, Node and Wasmtime pairs, with completed
owner checks. The cases cover all five receiver layouts; stored, default and
call sources; inline and outlined references; copied references; scalar operand
order; effects and defers; early return and loop continue; global owners; empty
values; guest memory growth; ordinary-reference elements; struct elements and
padding; live data namespaces; and LEB prefix boundaries at 0, 127, 128, 16383
and 16384. Default element effects run once per element and zero times for an
empty source.

The 112 image, owner and mutation-control checks cover complete Memory 0 and
data images, prefix bytes, capacity/length headers, padding, exact payload
bounds, live loop tops, declaration cleanup, separate data namespaces and
global persistent data. Valid damaged modules must fail a named assertion for
a wrong operation, short or long copy, wrong memory, changed padding, corrupt
prefix, early release, missing cleanup, wrong namespace allocator or wrong
global top. The source-padding test uses distinct bytes; the computed payload
retains its poisoned padding bytes rather than treating them as numeric leaves.
Only the identity byte of an empty temporary has no payload value contract;
the observers exclude that byte and check its reservation and cleanup.

The full Wasm suite passes 4,587 checks. The native baseline passes all 18
groups, including 2,676 frontend, 1,314 generated-C and 1,489 TinyCC checks.
All 52 exact shared-backend comparisons pass. All 1,070 unchanged parent O0/O2
Wasm fixture modules are byte-identical, using completed suite outputs without
guest reruns for the identity comparison. The tested executable matches the
frozen 78-file source set and all 5,298 validation inputs. Execution evidence is
from Linux. No timing or measurement lease was used.

## Preserved setup failures and limits

The first namespace mutation helper assumed a single generated function and a
dynamic namespace parameter. The compiler emits two functions with concrete
memory identities. The original failure remains intact. The corrected helper
selects the second generated function and substitutes the wrong allocator;
its observer rejects the live namespace tops. The four already-passed observer
groups were not repeated in the focused continuation.

A separate parent frontend control rejects a 256-element source for a u8 count
prefix with its exact range diagnostic. This is a valid rejection control, not
a runtime coverage claim. General element-layout changes, slices, nonfixed
by-value calls and other nonfixed temporary consumers remain separate work.

The runtime work is one payload copy for stored values. Computed values also
need the existing temporary evaluation and its payload storage. These costs
scale with the fixed element count. Prefix writes and owner/header setup use
bounded metadata. Performance and physical-memory measurements are outside the
correctness-only owner directive. No measurement lease was used.

Raw evidence is in `/tmp/goose-wasm-array-math-destinations-20261108`.
The [archive manifest](fixed-array-conversion/archive-manifest.json) records
frozen inputs, build identity, commands, preserved failures and final checks.
Binaries and complete generated artifacts remain in the raw directory.
