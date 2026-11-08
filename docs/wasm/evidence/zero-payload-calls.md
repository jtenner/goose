# Zero-payload fixed aggregate calls

The Wasm backend now accepts zero-length fixed arrays and exact empty variant
values as by-value parameters and results. The existing argument, parameter,
result and callback owners still reserve `max(1, image)` bytes. This keeps their
addresses distinct even when the payload image takes no bytes. The call ABI,
layout checks, Memory32 bounds and cleanup services are unchanged.

Three old guards rejected a zero image in call-value checking, storage planning
and callback parameter construction. Those guards are removed. Layout validation
still runs, and the original complete-owner checks still protect destinations.
The frontend forbids zero-size types as fields or elements under §3.4. No field
or element support is added. Empty structs already had a one-byte image and did
not need this change.

## Correctness evidence

Twenty-one native-valid families fail to compile on the parent Wasm backend.
They now pass at O0 and O2 in native code, Node and Wasmtime. The cases cover
direct and inline calls, callbacks, forwarding, assignment, discarded results,
projection, later-argument effects, defers, actual recursion, repeated cleanup,
distinct parameters passed from one source, and calls with data memory active.
Types include zero-length scalar, struct and ordinary-reference arrays and
several empty variant shapes.

Twenty Node observer/control checks pass. The Memory 0 observers poison source
identity, result and temporary slots, plus a sentinel outside the live owner
reservations. The three owned identity bytes have no payload value contract;
only those bytes may vary. The source byte and every other byte must match.
Observers check live caller/callee tops and the completed owner state. Valid
wrong-offset and missing-reservation modules fail named image or live-top
assertions. A separate loop checks each head; a valid missing-restore module
fails before final cleanup can hide it. A data-memory case checks the complete
persistent array image, its exact top, and the absence of an extra data memory.
A valid wrong-top module fails the owner-state assertion.

Twelve native/Wasm rejection checks retain the exact zero-size field and element
diagnostics at both optimization levels, with no partial output files. Four
older zero-size guard fixtures now require valid Node and Wasmtime output.
Their other layout and oversized-frame rejection cases remain checked. These
older helper groups still total 16 checks.

The full Wasm suite passes 4,205 checks. The native baseline passes all 18 groups,
including 2,586 frontend, 1,269 generated-C and 1,444 TinyCC checks. All 52 exact
shared-backend comparisons pass. All 1,028 parent Wasm fixture modules are
byte-identical using completed suite outputs, without guest reruns for the
identity comparison. Execution evidence is from Linux. No timing or measurement
lease was used.

## Preserved preparation failures and limits

Initial field fixtures were not valid language inputs. Both zero-length array
fields and empty variant fields are forbidden. Native compilation confirmed
these rejections. They remain rejection controls; no field ABI fix is claimed.
Five enum fixtures also used the full enum value `E.Empty` where an exact
`E.Empty` value was required. The corrected fixtures use `default<E.Empty>()`.
The original source, diagnostics and failed preparation records remain intact.

Read-only source searches checked reservations, incoming result ownership,
callback plans, parameter copies, matches, forwarding and cleanup. They found
no valid zero-byte subobject destination. A proposed private subobject hardening
change was therefore not made. Public inputs retain the frontend's field and
element guards.

Each empty owner needs one identity byte under the existing storage contract.
The runtime uses the existing frame allocator. There is no new persistent
compiler state or allocation service. Performance and physical-memory
measurements are outside the correctness-only owner directive.

The backend remains incomplete. Nonfixed array arithmetic destinations,
general layout conversions, slices, nonfixed value calls, remaining compound
lifetimes and host adapters are separate work.

Raw evidence is in `/tmp/goose-wasm-zero-call-20261108`. The
[archive manifest](zero-payload-calls/archive-manifest.json) records frozen
source/input hashes, compiler identities, commands, failures and final checks.
Binaries and full generated artifacts remain in the raw directory.
