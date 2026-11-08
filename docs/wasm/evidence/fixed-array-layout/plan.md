# Fixed-source to static-limited destination correctness gap

The current saved array-conversion compiler rejects five native-valid cases.
Parent raw sources, native emission/build/run and Wasm diagnostics are preserved
in parent01. All output statuses and module absence must be checked before a fix.
The baseline compiler identity is the saved array conversion build01 executable;
its exact source commit is pending completion of the current full validation.

Candidate scope: fixed-length array sources into static-limited receivers with
identical element layouts and count within capacity. Calls, stored values and
references share the existing complete fresh destination and bounded payload
services. Keep prefix and unused capacity bytes distinct from active payload.
Nested owners, parameter/result/assignment consumers, source effects, aliases,
early exits, zero payload and padded element types need coverage.

No timing or measurement lease. Do not widen to general element or nonfixed
source-layout conversions in this change.

## Narrow implementation plan after the current checkpoint

- Recognize only A_FIXED source to A_LIMITED receiver with identical element
  layout and source count within receiver capacity.
- Keep RequireFixed and complete fresh-owner validation. Copy only the active
  source payload into the existing array payload offset, then store its count.
  Leave unused capacity and padding outside the copied image unchanged.
- Route mismatched fixed call results through the existing temporary before
  this copy. Keep exact-layout calls on their current destination path.
- Let stored/reference values use the existing read-place service. Apply the
  same copy authority to local, parameter/result, assignment and child owners.
- Test ordinary references, readonly values, empty sources, struct padding,
  nested Memory 0 and data-memory destinations, callbacks, later effects and
  cleanup. Each new accepted case must be native-valid on the saved parent.
- Valid damaged modules must prove the image observers detect payload overrun,
  wrong prefix, wrong source and early owner release.
