# Fixed aggregate array prefixes and fresh unused slots

The direct Wasm backend now constructs fixed aggregate data arrays with u8,
u16 and u64 length prefixes. The existing u32 path remains. Struct, enum and
variant elements use the existing checked fixed layout and copy services.
The parent is `06ba2c50db69ea6b8ff8b424bfdca2a57b3a8570`.

The tested Release compiler SHA256 is
`58a43a2e43b14a7896ab96bdc95c2e4b7f062eb3529b83351f8c50340c5ef491`.
Both Release builds, the assertion-enabled builds and their source hashes are
retained. The first Release prototype predates the unused-slot fix.

## Prefix construction

`DataNominalArray` admits the fixed unsigned prefixes. `ReserveFreshDataArray`
uses the receiving prefix size and rejects literal counts that do not fit it.
The existing memory32 extent check remains. Element addresses, nested fields,
references and copied iteration binders use the existing layout services.
No new array descriptor, compiler table or general value-call ABI is added.

Fifty-eight native-valid program families fail the parent Wasm admission check.
They cover all three new widths, empty and nonempty literals, exact copies,
fixed and limited sources, conversions between stored prefixes, nested fields,
references, reference fields in data elements, globals, recursive iteration,
enums, variants, FP bit values, cleanup and counts 255 and 256.

## Confirmed unused-slot error

Before widening admission, a dirty-memory observer exposed a separate error in
the accepted parent and the first prototype. Repeated fresh construction of a
short limited array left values from its previous use in unused slots. A valid
retained element reference returned 3 instead of native value 0. This also
affects Memory 0 arrays, without a data-memory owner.

Seventeen native-valid families reproduce wrong results in the parent. They
cover partial and empty numeric, reference and nominal literals, fills,
defaults, FP and Boolean values. Zero-count fills still evaluate their value
once. Empty nominal defaults do not run inactive element defaults. A separate
stored whole-value copy must preserve an explicitly written unused slot.

`ZeroUnusedInlineArray` clears only the unused suffix after successful fresh
construction. It checks the fixed owner extent and keeps the memory identity.
Full literals emit no clear. The call sites cover scalar/reference literals,
byte strings, fills, nominal literals and default construction. Explicit
capacity constructors keep their existing uninitialized storage policy.
Stored copies keep their source bytes and do not use this clear.

## Image checks and fault controls

The focused run has 77 program families, with native, Node and Wasmtime checks
at O0/O2. The assertion-enabled compiler must emit the same 154 modules as the
Release compiler. Completed owner checks also inspect Memory 0 and data tops.

The 64 image and rejection checks include complete Memory 0 and data images,
all three new prefix widths, unused zero bytes, sentinels, live and completed
tops, and dynamic data-memory identities. A second dynamic call keeps a caller
owner live and poisons its free region. This detects writes to the wrong data
memory. The accepted parent passes the dynamic program's active-value checks
but fails its first complete dirty-image check.

Validated damaged modules change counts, field offsets, suffix clearing,
memory identity, reservations and cleanup. Each must fail the assertion for
that specific fault. Unsigned LEB nominal arrays and aggregate data fills
retain their exact pending-feature rejection.

A 256-element u8-prefix literal is rejected by the shared frontend before
native or Wasm emission. Four O0/O2 checks require that exact range diagnostic.
This is a frontend limit check, not a runtime backend-guard result.

Failed helper attempts are preserved. They used an old runtime helper name,
assumed an aligned header store, or treated an empty struct as zero-size. An
empty struct has one byte; a zero-length struct field is rejected by the
frontend. Those inputs do not prove a zero-stride backend path. No production
change was made to satisfy those failed test assumptions.

## Full-suite execution record

The owner stopped the second full run for the GC profiling quiet hold. Its
exit -15 and partial results remain. After explicit release, all source, test
and compiler hashes matched. The third run completed every core unit and every
fixture comparison, then failed an older aggregate-fill image observer. That
observer expected poison in an unused fresh Cell instead of the native zero
bytes. Its original model and complete failure remain.

The model now expects exactly those three suffix bytes to be zero. A new
validated omitted-clear control must fail the same complete-image assertion.
No other image comparison was removed. The old one-byte long-copy mutation
is now erased by the required clear. Its replacement crosses a poisoned
boundary sentinel and must fail the complete-image check. A remaining-only continuation
verifies the observed completed-prefix control flow, all frozen hashes and
1,754 fixture-module identities. It then executes every later helper afresh.
The first continuation stopped before tests on a setup name check. The next
reached the masked long-copy control. Both failures remain. The final
continuation is separate, with 32 construction-image and ownership checks
verified first in a dedicated unit. Reuse records identify both phases. No stopped or
failed run is called a complete pass.

## Final verification

The [final record](aggregate-prefixes/final-validation.json) records 6,729 Wasm
checks across the verified completed fixture phase and the final helper phase.
All selected checks passed. The native baseline passed all 18 groups, including
3,262 frontend, 1,607 C and 1,782 TinyCC checks. All 52 shared-backend exact
comparisons passed. The assertion-enabled compiler emitted 154 modules identical
to the matching Release modules.

Of 1,592 parent fixture modules, 1,252 are byte-identical. The other 340 each
contain new unused-slot clear sites. Their test sources are unchanged. The
final record verifies all 85 compiler source files and 5,825 test/script inputs.
Raw records remain under `/tmp/goose-wasm-aggregate-prefix-20261108`.

The later helper phase also found an older nested-array data observer that
expected poison in four fresh unused bytes. The model now expects zero there,
with an added validated omitted-clear control. The construction and nested-data
model units pass 32 and 10 checks respectively. Complete image assertions,
active bytes, sentinels, memory identity and cleanup controls remain in force.

## Costs and limits

This work is correctness only. No performance test or measurement lease is
used. The suffix clear writes bytes in proportion to unused capacity. That
work is necessary to match the native fresh-value semantics. It adds no
logical owner reservation. Compiler allocation, runtime cost and physical
memory use are not measured.

Nonfixed fields and value calls, aggregate LEB prefixes and data fills, slices,
relative references and host/worker compilation remain separate work. The
backend is still incomplete.
