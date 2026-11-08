# Copies between stored array prefix layouts

The direct Wasm backend now copies a stored variable array into a receiving
array with a different length-prefix layout. This includes fixed unsigned
prefixes, unsigned LEB prefixes, growable receivers and runtime-limited
receivers. Source and receiver must have matching supported element types.
The parent is `1fae1779b7345fd6a4391d6e3c9bfe617dd775c2`.

The tested Release compiler SHA256 is
`c2b778ea76352c814f17df7325c431148b2443ed0cc02d47afb3f7138d44753a`.
Source hashes, both compiler builds and assertion-enabled flags are retained.

## Conversion

`InitCountedArrayValue` extends the existing static limited-array constructor.
Its stored variable-source path uses `ActualType`, checked read places and an
`ArrayView`. The count and any LEB prefix width are captured once. A checked
zero-index element address gives the payload address before the receiver is
allocated. The packed source memory identity is retained, including references
stored in fields of data elements and references returned by calls.

The receiving prefix is computed from its own layout. A narrow receiving count
field gets an unsigned range check. Count times element stride is checked before
multiplication; prefix plus payload is checked before allocation. The conversion
writes the receiving header and copies only the active payload. Runtime-limited
receivers get capacity equal to the active length. Growable headers stay in
Memory 0. Data-array pointers stay in their existing Wasm locals.

Existing exact-layout copies keep their old path. The static limited-source
path also keeps its old emission. No new compiler field, table, array descriptor
or general nonfixed argument/result ABI is added.

## Failing-first and focused checks

Forty-six final program families pass the preserved parent native compiler and
fail its Wasm array-adaptation check. The verifier checks each original command,
exit status, source hash and native output against the final fixture. The first
reference probe had `&=` without a separating space. Its frontend rejection is
preserved; the corrected native-valid probe is separate.

The focused run has 92 native/Node/Wasmtime pairs at O0/O2, with completed
Memory 0 and data-owner checks. Cases cover stored prefixes, LEB source and
receiver, empty arrays, counts 127, 128, 255, 256, 16384, 65535 and 65536,
reference elements, stored references, indexed references, reference fields in
data memory, ordinary and inline reference-return calls, globals, loop cleanup,
dynamic source memory identities and source effects evaluated once. Copies are
checked for independent element storage; reference pointees remain shared.

An assertion-enabled compiler emits and runs the same 92 pairs under Node.
Every module must match its Release module byte for byte.

## Full-image checks and controls

The healthy image observer checks fixed-width, LEB source, LEB receiver, empty
and u64-source cases. The source stays live after the copy. It seeds future
receiving storage and adjacent sentinels, then compares complete Memory 0,
source data and receiving data images. Live and completed stack tops are
checked. A Memory 0 sentinel also proves that the data copy does not write there.

Validated damaged modules change payload length, source memory, prefix width or
LEB continuation, Memory 0 bytes, source cleanup and receiving cleanup. Each
must fail the assertion for that specific damaged behavior. These image runs
and controls contribute 76 checks.

Four O0/O2 range cases use native-valid programs with lengths 256 and 65536 that
exceed the u8/u16 receiving prefixes. Native execution must report its exact
stored-length range error. Node and Wasmtime must report
`array length exceeds stored prefix`. The image observer checks that no receiver
was allocated or written. Inverted guards must fail at the following print.

A separate adversarial observer changes an exposed u64 source count from 3 to
536870912, with stride 8. It must report the data-size error before allocation.
The source image, complete Memory 0 and receiving image remain unchanged after
that controlled mutation. An inverted product guard must fail the observer.
This is a damaged-memory check, not a native-valid value comparison. A failed
activation is consumed; terminal unwind cleanup is not claimed.

The complete helper run has 90 image, range, cleanup and guard checks.

A separate raw source uses a u32 source and u64 receiver. At O0/O2, native,
Node full images and Wasmtime agree. A damaged source count of 536870911 with
stride 8 fits the payload product, but adding the receiving eight-byte prefix
overflows memory32. Both observers require the controlled data-size error before
allocation. Both validated inverted sum guards instead reach an out-of-bounds
bulk copy and are rejected for that specific error. These two extra pairs and
four adversarial checks are recorded in `sum01`, outside the full-suite count.

## Known aggregate blocker

The first focused run stopped at a native-valid padded-struct array. Its u8
source prefix is outside the current `DataNominalArray` admission policy, which
permits only u32 prefixes. It failed before the new copy ran. The source, native
pass, candidate failure and original helper remain unchanged. It is excluded
from the supported positive families. Two explicit O0/O2 checks retain the exact
compound-layout rejection. Fixed aggregate prefixes are the next separate
compilation task, including fresh child bounds and copied iteration binders.

A read-only native worker searched source address, prefix, range and lifetime
paths. It found no confirmed hole in the narrow scalar/reference conversion.
It ran no build, guest, measurement or lease action. Its source notes are
separate from execution evidence.

## Final checks and limits

The [final record](array-prefix-conversion/final-validation.json) records actual
6,199 Wasm checks, 18 native groups, 52 exact comparisons, 1,500 unchanged
parent modules and source/test/compiler identities. Native groups include 3,108
frontend, 1,530 C and 1,705 TinyCC checks. Raw records remain under
`/tmp/goose-wasm-array-prefix-conversion-20261108`.

This work is correctness only. No timing, measurement lease or performance
acceptance is used. The new constructor uses a fixed number of locals and the
existing allocation path. Payload storage and copy work grow with active byte
count because the result is an independent value. LEB loops are bounded by the
checked memory32 count. No compiler-allocation or physical-memory claim is made.

Growable and runtime-limited sources, nonfixed value results, aggregate non-u32
prefixes, nonfixed fields, pools, relative references, slices, byte views and
host/worker compilation remain separate work. The backend is still incomplete.
