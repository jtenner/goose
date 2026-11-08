# Fixed array values from blocks and conditionals

The direct Wasm backend can now construct a nonfixed array from a plain block
or conditional whose completing branches have the same fixed array layout.
Both fixed-length and static limited-array sources are supported. The receiving
array can use the existing variable, growable, runtime-limited or unsigned LEB
layout. The parent is `c423808c123e8b4b89d82f2640838ac86fe2f21c`.

The tested Release compiler SHA256 is
`f1f5b1d4f36560e6c51cb8b10832282a77c63b09f2fe3c515f28260d682628e6`.
The build, source hashes, test inputs and assertion-enabled build are retained
in the archive.

## Source layout and lifetime

The type checker can adapt the expression type to the receiving nonfixed array.
The source layout must still come from the value before that adaptation.
`FindFixedArraySource` follows only plain block tails, conditional branches and
explicit copy operands. Each completing value must have the same fixed array
type. A checked void branch supplies no value. Mixed capacities, mixed layouts,
value loops, early blocks and matches remain rejected.

The general `ActualType` service is unchanged. Stored references and already
known fixed layouts keep their old read-place paths. Only a recovered source
uses a fresh fixed temporary and `ConstructFixed`. The existing block and
conditional construction services copy the result before deferred actions and
scope cleanup. The receiver then uses the existing fixed or limited conversion
service, with its own destination prefix and memory identity.

The source temporary has its own cleanup scope. An early function or inline
return restores that scope. The receiving allocation belongs to the receiving
declaration, not to the source temporary. A completed source cleanup therefore
cannot release a live receiver. Global receivers keep their persistent lifetime.

## Failing-first and focused checks

Thirty final fixture families are native-valid. Twenty-six fail with the
parent's missing array-value lowering message. Four already pass in the parent
and serve as reference and call-result regressions. Two exploratory inputs use
`copy` on a reference temporary and fail in the native frontend. Their original
records are kept, but they are not positive fixtures.

The focused checks execute all 30 families at O0 and O2 in native code, Node
and Wasmtime. They also check completed Memory 0 and data-memory ownership.
Cases include nested blocks, runtime conditionals, else-if branches, fixed and
limited counts, global receivers, growable/runtime/LEB receivers, deferred source
mutation, reference-element identity, void branches, function returns and opaque
inline returns. The opaque boolean input prevents O2 from removing the tested
inline return path.

The assertion-enabled compiler compiles and executes the same 60 pairs under
Node. Each module must match its Release module byte for byte.

## Full-memory observers and controls

The deferred-source observer seeds the complete private source snapshot, source
spare capacity, future data storage and a sentinel. It checks that the receiver
gets the pre-defer value while the original source contains the deferred change.
Full Memory 0 and data images are compared at the live checkpoint and completion.
Both source temporary and receiving stack tops are checked.

The inline observer checks two opaque calls in one activation. The first takes
an early inline return. The second constructs the array. Each print must see only
the enclosing two-byte boolean frame. Complete memory images and final stack
restoration must match. A damaged cleanup must fail a specific live or completed
stack assertion.

Healthy runs and validated damaged modules provide 36 image and control checks.
Controls change the source of the payload read, copy length, source reservation,
temporary cleanup and receiver cleanup. Four further native-valid O0/O2 checks
require exact rejection of mixed fixed lengths or limited capacities. A valid
module or unrelated error cannot satisfy these controls.

The first observer run failed because its expected error text covered only the
live stack check. The damaged cleanup instead failed the completed stack check.
The corrected helper names both specific failure points. The original helper,
module, stderr and exit status remain in `image01`; the final run is `image02`.
There was no compiler change for this test repair.

## Final verification and limits

The [final record](array-expression-source/final-validation.json) records actual
5,833 Wasm checks, 18 native test groups, 52 exact comparisons, 1,440 unchanged
parent modules and frozen-source checks. Native groups include 3,016 frontend,
1,484 C and 1,659 TinyCC checks. Raw files remain under
`/tmp/goose-wasm-array-expression-source-20261108`.

This is correctness-only work. No performance measurements or lease actions
were used. The new source classifier visits only the value tree at construction
sites and uses no added compiler heap storage. The existing private snapshot and
copy need storage and work proportional to the fixed source layout. That copy
is required to preserve the value across deferred source changes. No runtime,
compiler-allocation or physical-memory claim is made.

Mixed source layouts, value matches and loops, copies between different nonfixed
prefix layouts, general nonfixed array arguments/results, nonfixed fields, pools,
relative references, slices and byte views remain separate work. The full backend
is still incomplete.
