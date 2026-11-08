# Exact stored array assignment

Fixed arrays and arrays with static limited capacity now support whole-value
assignment from an addressable value with the same stored type. Owner, field,
index and reference destinations use the existing checked place and byte-copy
services. The copy includes the limited-array length, active elements and
reserved capacity. Reference elements remain shallow copies. The destination
place is captured before the source is evaluated. Self-copy and overlapping
memory retain the existing memory.copy semantics.

The change adds no persistent compiler field or runtime descriptor. One
assignment copies its complete fixed image. It does not add an element loop or
heap allocation. Hostile opaque references keep the existing null, memory
identity, low-u32 address-carry and full-copy memory bounds checks. An arbitrary
opaque reference is not a separate proof of its source object's declared extent.

Twenty-eight native-first O0/O2 cases passed natively and stopped at the prior
Wasm assignment guard. They cover fixed/limited scalar and nominal arrays,
reference elements, data fields, source/target side effects, empty arrays,
index effects, field offsets and opaque self-copy. Both Wasm engines now pass.
The complete Memory 0 observer seeds reserved capacity and checks the exact
copied image and neighboring fields. Valid short, long, omitted and wrong-source
mutations fail its specific image assertion. Nine validated reference faults
at both optimization levels run in both engines. These include source/target
null, invalid identity, end-of-memory span, address carry and wrong namespace.

The read-only review found no confirmed backend defect. It found a stale
admission-table expectation, reproduced as a failing test before correction.
The same input now runs as an accepted native/Wasm case. Additional image,
reference-fault and index/field-effect checks were added after that review.
The review predates the default-count fix below, which is covered by its own
failing-first regressions. No later review coverage is claimed.

## Default source counts

A later native-first check found a real wrong-result bug in fresh default-array
construction. A fixed default converted to a wider limited array used the
limited destination's default length, zero, instead of the fixed source count.
Six basic O0/O2 cases print two natively and zero with the prior compiler.
Twelve further cases fail the specific count assertion with that compiler;
two empty-default controls already pass. The corrected code uses the declared
source count and checks it against the destination span before construction.
It preserves one default evaluation per element, no evaluation for an empty
default, optional-reference zero values and the old assignment target during
constructor evaluation. All twenty cases pass in Node and Wasmtime.

Seven permanent source families cover side effects, fresh data fields, one-,
two- and four-byte length prefixes, zero counts, optional references and reads
of the old target. Scalar and nominal element images use the same count proof.
Different element stored types remain guarded. A proposed u8-to-u16 default
conversion is rejected by the native frontend and is recorded as language
policy, not as backend rejection coverage.

## Scope and evidence

Fresh array literal/default assignment, different-layout assignment, data-array
owner replacement and general by-value array calls/results remain separate
compilation work. The nonfixed-array owner replacement fixture is rejected by
the language's frozen-construction rule. Capacity-changing reference views
are also frontend-invalid. Neither supplies runtime backend coverage. An
original image fixture used the reserved word guard; only its corrected
sentinel form is counted.

The final correctness-only suite passes 2,003 groups, including the forty
complete Memory 0/data matrix cases. The native baseline passes 1,958 frontend,
955 generated-C and 1,127 TinyCC groups, plus all other baseline groups. All 52
exact comparisons pass; all 406 unchanged-source parent module pairs are
byte-identical. The compiler SHA256 is
`745b87e7e925e8532d40fdc1f11ddf4c980e978a164d907f7d2a32d1e7389375`.
All 73 source files and 4,533 source/test inputs match their frozen hashes.
The first stored-array compiler passed 1,961 Wasm checks before the default-count
bug was found. That result remains separate and is not final validation for
the repaired compiler.

Selected records are retained in the
[archive manifest](array-assignment/archive-manifest.json). Raw records remain
under /tmp/goose-wasm-array-assignment-20261107 and
/tmp/goose-wasm-default-adaptation-20261108. All work is correctness-only.
No timing, measurement lease or performance acceptance gate is used.
