# Stored nonfixed array source conversion

Parent compiler is aggregate-prefix build02, SHA256
58a43a2e43b14a7896ab96bdc95c2e4b7f062eb3529b83351f8c50340c5ef491.
Its commit will be recorded after the current increment passes and is committed.
Four parent-first native passes and exact Wasm conversion rejections are retained.
No implementation build has run for this plan.

Extend only InitCountedArrayValue's stored-source classifier from VariableArray
to DataArray or IsResz, still excluding exact matching layouts. Keep the same
scalar/reference element equality and existing admission checks. Rename the
local classifier to nonfixed; no compiler member, descriptor or new allocation.

WithReadPlace resolves a stored growable owner to its Memory 0 header.
ArrayFromPlace retains the header's Memory 0 proof and marks elementMemory=-1.
CaptureArrayView captures active length once. ElementOffset at zero loads the
packed payload pointer from the header, before any receiving allocation.
Runtime-limited sources use their own eight-byte prefix and packed data identity.
The existing width, payload-product and prefix-sum checks remain.
Receiving runtime capacity is active length, not source capacity.
Exact-layout copies retain their existing full source capacity semantics.

Required correctness cases: both source layouts; variable fixed/LEB, growable
and runtime-limited receivers; empty/default sources, spare capacity and pop;
references and reference-return calls with one-time effects; reference elements;
all scalar widths/FP bits; globals, loops and dynamic call-stack namespaces.
Full images must show separate header and source data images, active payload
only, receiver cleanup and source lifetime. Native and Wasm range failures
must identify the receiving prefix before allocation; damaged counts must
fail the specific byte-size guard. Add damaged memory/count/offset/cleanup
controls. Verify exact copies remain unchanged. No timing or profiling.

Block/conditional nonfixed values, general array value calls, aggregate
growable/runtime layouts, slices and stage F adapters remain outside this change.

## Existing guard retained

WasmValueSupport::ScalarElement excludes references to growable owners in
array elements. The grow_indexed_reference sketch is therefore an expected
compound-element rejection, not a new conversion positive. Runtime-limited
owner references do not use IsResz and retain their existing supported path.
The implementation must not broaden ScalarElement or nominal-field admission.
