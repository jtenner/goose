# Next correctness increment

Parent: the tested constructor-assignment source, to be committed after its final suite.
Native-first evidence: parent-first/results.json, sixteen valid O0/O2 native cases and exact current fill/default guards.

Scope: inline fixed/limited arrays with positive fixed nominal elements. No data-array fill, adaptation, push/pop, general by-value ABI or zero-stride expansion.

Reuse FreshFixedDestination and WithFixedTemporary. Validate capacity/count and complete owner span before emission. Emit a bounded copy loop through packed addresses, so fixed arrays nested in data elements retain their actual memory identity. No new compiler fields or runtime descriptors.

For fill, construct one element temporary before the loop, even at count zero, and copy its complete stored image into each element. For fixed-array default, construct and release one element temporary inside each loop iteration. A limited-array default stores count zero and evaluates no element. Each temporary is registered for ordered cleanup before any initializer.

Use the frontend's checked B_DEFAULT defaultinit node for element defaults. Do not clone AST or reconstruct defaults in the backend. Preserve early returns and loop exits through the existing cleanup mechanism. Do not assert native equality of inactive enum padding.

Add native-first constructor/field/data-field tests, zero-count side effects and early exits, reference identity, enum active values, nested fills, cleanup and a copied Memory 0 image model with damaged-copy controls. Promote only exact existing fill/default admission cases. Keep complete Memory 0/data matrix, full native/Wasm correctness, exact outputs and compiler provenance.

Correctness only. No timing, measurements, performance gates or lease rotation.
