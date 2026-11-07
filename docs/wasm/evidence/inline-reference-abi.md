# Canonical packed inline-array references

Functional and static validation passed. Independent review found no
production ABI defect and one test-observer defect. Its failing-first repair,
callback-result coverage and final 1,073-check suite pass. Performance acceptance
remains open. This increment does not complete Stage D or the backend.

## Scope

When the completed storage plan uses data addresses, ordinary references now
use one i64 memory/offset representation. This includes fixed and static-capacity
limited arrays. Only true growable-array owner-header references retain the i32
ABI. Thin programs retain i32 ordinary references. The rule is set before
function declarations and does not vary per call.

The internal borrowed-array transport changes with the reference ABI. Reads,
params/results, addressed spills, globals, stored references, optionals,
null/identity checks, direct/inline/callback results, field places, copies,
mutable walks, iteration and byte-print snapshots use the same representation.
Physical frame addresses remain i32. Stored ordinary references retain eight
bytes; owner descriptors retain their existing sixteen-byte layout. Array
prefixes, nominal field offsets and frame ownership rules do not change.

By-value array calls/results, fresh aggregate data construction and other
pending layouts remain guarded. Growable-owner reference fields remain an
exact-diagnostic rejection control. Copied aggregate loop binders still use a
planned fresh Memory 0 destination. A packed source no longer proves Memory 0,
so the existing checked copy-to-frame service handles opaque source identities;
this does not admit variable/data aggregate-array values.

## Provenance and checks

Parent: `4c302e7ad2cebaae82ae18a08e9978329cc571a2`, compiler SHA256
`5b68b041c3aba5c6bd6a6fa7e96a0b5a8aa5cc5558761b56efa5d83cacb1599a`.
Candidate compiler SHA256:
`bcc336c9f3f06f604b6ecdb002f4f355dae24bca9691e5d1b16ca30dfef7148c`.
See [frozen identity](inline-reference-abi/build04/build-identity.json) and
[source hashes](inline-reference-abi/build04/source-hashes.json).

The focused matrix has 16 families at two optimization settings. Two passed
parent thin cases and their native references are verified reuses from build03;
30 parent and 32 candidate cases ran in build04. Source, module, status, output
and memory hashes are checked before reuse. Node records all exported memory
bytes after synchronous completion. These focused modules export no Wasm
globals: their empty global lists do not observe stack tops. Goose source globals
in Memory 0 are part of the memory comparison. The original post-run owner
assertion ran after host cleanup and is withdrawn as guest-cleanup evidence. All 32 candidate images match the parent. Wasmtime checks expected
output and in-program assertions; it does not supply these full image checks.
All 26 signature assertions pass, including thin growable-header params/results.
The new thin fixture's two modules are byte-identical. See
[parent records](inline-reference-abi/build04/parent/case-results.json),
[reuse record](inline-reference-abi/build04/parent/reused-parent-results.json),
[candidate records](inline-reference-abi/build04/candidate/case-results.json), and
[shape output](inline-reference-abi/build04/abi-shapes.stdout).

The original [Wasm suite](inline-reference-abi/full-wasm01/full-wasm01.stdout)
passed 1,062 check groups. After the observer repair and callback additions, the
[final suite](inline-reference-abi/full-wasm02/full-wasm01.stdout) passed 1,073
check groups, not 1,073 distinct programs. Its frozen compiler source and 4,202
validation inputs matched before and after. The full
[native baseline](inline-reference-abi/native-baseline01/native-baseline01.stdout)
passed, including 842 generated-C checks and 1,014 TinyCC runs. Existing
layer/GPU/platform and unsupported-JIT skips are retained. Both units checked
source, executable and the original 4,196 validation-input hashes before and after.
The final suite also generated and ran native C references for the new callbacks;
the earlier full native baseline was not repeated after these test-only changes. All
[52 older-checkpoint comparisons](inline-reference-abi/compatibility01/compatibility01.stdout)
also passed; these compare generated outputs, reports and diagnostics.

The [226-pair inventory](inline-reference-abi/compatibility01/prior-module-deltas.json)
reuses saved immediate-parent modules after hash verification and reads candidate
modules from the successful full suite. It is not a new parent execution. There
are 172 identical and 54 changed pairs, with total module byte delta -313.
The largest growth is 83 bytes and largest shrink is 253 bytes. This is static
size evidence, not a throughput result or a universal compatibility proof.

## Static costs and limits

[Per-module metadata](inline-reference-abi/module-structure-deltas.json)
records type, param/result, local, helper and code-section changes for all 54
changed pairs. It does not decode or semantically audit every instruction.
Added helper kinds are checked memory loads/stores and copy-to-frame dispatch.
Removed thin-memory narrowing checks and casts can offset those additions.
The total code-section delta is +405 bytes despite total module delta -313.
Total local-slot deltas range from -1 to +6 across changed pairs; these totals
include helper functions and are not per-source-function scratch counts.
Known owner and field memory facts still use direct paths where proved.

The source adds no per-reference heap wrapper, AST clone or unbounded function
specialization. Opaque packed references can add checked dispatch where a thin
ABI implied Memory 0. Code/helper size, engine initialization, guest access/call
cost, compiler CPU/allocations/RSS and physical memory remain unmeasured. Equal
bytes, addressable pages or logical tops do not prove physical-memory release.
Current source inline owners remain in Memory 0. Later fresh data destinations
need valid nonzero inline source construction and lifetime tests before admission.
Native validation is Linux-only; no cross-platform runtime result is claimed.
See the [cost audit and queued handoff](inline-reference-abi/abi-cost-audit.json).
A fresh coordinated scope, lease, host/affinity controls, repetitions/warmups and
qualified decision limits are required. No prior scalar timing grant is reused.

## Review and owner-observer correction

The independent [Astra report](inline-reference-abi/review/report.md) found no
confirmed production ABI defect. It found a P2 test defect: the Node adapter
cleared print and snapshot owners before the new completion assertion read them.
The saved output, memory, signature and module-size records remain valid.

Before repair, two valid damaged modules retained a print owner or snapshot
owner while preserving expected output and memory. The original observer
accepted both. The repaired adapter has an optional completion hook after guest
return and before its unchanged terminal cleanup. The test hook reads both
actual owner counts once. The same acceptance check now rejects each damaged
module at its intended assertion. Direct controls record pre-cleanup counts
(1,0) or (0,1), then terminal counts (0,0), equal output and equal memory.
See [failing-first records](inline-reference-abi/owner-before01/before-results.json),
[passing controls](inline-reference-abi/owner-after01/owner-controls-results.json),
and the [resolution record](inline-reference-abi/review-resolution.json).
All 32 saved parent/candidate Node pairs were rechecked with the fixed observer;
all 64 runs observed zero owners and preserved their original image bytes.
No C++ compiler rebuild was needed for this test-only repair.

The default adapter adds one optional terminal hook check. It adds no callback
allocation in ordinary runs, no guest import, and no guest instruction. The
extra observation is once per completed instance, outside guest loops. The
measurement handoff must use the same corrected adapter on both compilers.

The original review read all 135 staged files. Nine unchanged context files have
unread ranges. Binary section and byte checks are not a full opcode audit; the
report and inventories state those limits. The review also identified missing
callback-reference result coverage. Two new fixtures now pass at O0/O2 in
thin and packed modes, using valid named function values and nullable checked
blocks. Eight parent/candidate cases pass both engines, four native references
pass, all four memory-image pairs match, and thin modules are byte-identical.
All 24 emitted specializations in 16 signature families use the expected ABI;
see [callback cases](inline-reference-abi/callback-results03/case-results.json).
One passed parent thin case supplies three verified reused outcomes; 17 guest
outcomes ran in the final continuation. Non-null fixed-array block
tails copy by language design and are not a reference-result control.

The original cost-audit JSON is retained unchanged. Its statement that corpus
deltas were pending is superseded by the completed 226-pair inventory and the
54-row metadata report above. No controlled cost or physical-memory result is
claimed.

## Preserved fixture and setup failures

Build01 used a repeated optional field read that the checker does not narrow.
Build02 passed native validation but used an out-of-line callback capture
unsupported by the Wasm parent. Build03 passed both thin cases, then the parent
rejected a growable-owner reference field under the existing target guard.
No candidate build began in these attempts. The final fixture narrows a captured
local optional and uses only its callback parameter. Its header control uses
supported locals, params and returns. The original owner-field source is
native-valid and supplies the exact-reason rejection control. Failed records
and fixtures remain separate; the passed thin cases are reused without rerun.

The first callback-result fixture used a fixed-array block tail, which copies by
language design. Native checking rejected it before candidate execution. The
next valid fixture passed its first parent case, then a shape parser wrongly
required one nullable specialization; separate callback literals produced two.
The corrected parser checks each emitted signature and reuses the passed case.
These harness failures are preserved separately from compiler results.

[Archive hashes](inline-reference-abi/archive-manifest.json) map copied records
to complete raw evidence under `/tmp/goose-wasm-inline-ref-abi-20261107`.
Prepared plans remain plans; their status text does not replace command exit,
producer results, owner/reaping records or the final release probe.
