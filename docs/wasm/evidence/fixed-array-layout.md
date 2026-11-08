# Fixed sources into static-limited array construction

The Wasm backend now constructs a static-limited array from a fixed array with
the same element layout when its count fits the receiver's capacity. Stored
values, copied values, reference results and fixed call results use the same
checked fresh destination. Exact-layout calls and copies keep their old path.

The copy uses the existing checked array payload child after the receiver's
count prefix. It copies only the active fixed image and then stores its count.
Unused capacity stays unchanged. An empty payload does not receive a standalone
identity-byte store. A call whose declared result has a different layout first
lands in its intrinsic fixed temporary, then uses this payload copy. This keeps
callee result ownership separate from the receiver's layout.

The new predicate is limited to fixed sources and static-limited receivers.
The shared construction path covers fresh local, parameter, result, callback
and aggregate-field destinations. Whole-array assignment keeps its existing
exact-layout guard. Nonfixed sources and different element layouts remain
separate work.

## Correctness evidence

Thirty-one native-valid fixture families fail to compile on the parent Wasm backend. One
additional callback family already passes on the parent and remains regression
coverage. The candidate passes all 64 O0/O2 pairs in native code, Node and
Wasmtime, with completed owner checks.

The cases cover stored and copied values, ordinary and readonly references,
outlined and explicit inline returns, defers, later-argument effects, limited
parameters and declared results, typed callbacks, actual recursion, early
return and continue, globals, ordinary-reference and padded-struct elements,
fields in Memory 0 and data arrays, effectful selection of a data source,
empty sources and 255/256-capacity count-prefix boundaries.

Thirty-two image and control checks pass. The Memory 0 observer checks the
complete source, receiver, unused capacity, source-result temporary and outside
sentinel. It checks live and completed frame tops. The data observer checks a
complete data-array element with a leading u8, a 256-capacity limited field and
a trailing u16. It checks the full data image, two-byte count, unchanged spare
capacity, adjacent values, outside sentinel and owner tops. Valid short-copy,
long-copy, wrong-count, wrong-prefix-width, missing-restore, early-release and
wrong-memory modules must fail named assertions.

The final full Wasm suite passes 4,811 checks. The native baseline passes all
18 groups, including 2,740 frontend, 1,346 generated-C and 1,521 TinyCC checks.
All 52 exact shared-backend comparisons pass. All 1,160 unchanged parent O0/O2
Wasm fixture modules are byte-identical, using completed suite outputs without
guest reruns for the identity comparison. The tested executable matches the
frozen 78-file source set and all 5,365 final validation inputs. Execution
evidence is from Linux. No timing or measurement lease was used.

## Preserved setup failures and limits

The first focused run completed native, Node and Wasmtime for its first case,
then selected the data-memory owner mode for a Memory 0-only program. The
continuation verifies and reuses those passed results and runs the missing
owner check in the correct mode. The original failed mode is retained.

The first image observer used a host property that does not exist. The fixed
observer uses the instance's exported memory. Its first long-copy control then
exposed a weak poison pattern: source-adjacent bytes and unused receiver bytes
had the same value. The next observer uses distinct bytes, and the valid long
copy fails the full-image assertion. Both failed helpers and records remain
intact. No production-source change was made for either setup failure.

The first full suite stopped at an old field-adaptation rejection that now
compiles. The admission scan also found stale fixed-array copy, aggregate-array
and call-result guards. Sixteen old checks now require successful Node and
Wasmtime execution, with their native execution or frontend checks retained. The direct guard checks retain the nonfixed result rejection
and all six large-layout limits. A separate helper attempt passed its six
array-result checks, then stopped because its aggregate helper arguments were
in the wrong order. The continuation runs only the unfinished groups. The
original helper, records and first full-suite failure remain intact.

A read-only source search found no confirmed defect in the payload child or
empty-value paths. It identified missing parameter/result, callback, data-child,
wide-prefix and effect coverage; those paths are in the final matrix.

The runtime copy work scales with the active fixed payload, not receiver
capacity. Mismatched call results also use one existing intrinsic-type temporary.
Stored sources do not need that extra temporary. No new persistent compiler
storage or allocation service is added. Performance and physical-memory
measurements are outside the correctness-only owner directive.

Raw evidence is in `/tmp/goose-wasm-fixed-result-layout-20261108`.
The [archive manifest](fixed-array-layout/archive-manifest.json) records source,
compiler, inputs, commands, preserved failures and final checks. Binaries and
complete generated artifacts remain in the raw directory.
