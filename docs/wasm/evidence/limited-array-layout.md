# Limited-array layout conversion correctness

This change lets a fixed-storage limited array initialize or replace a limited
array with a different capacity. Both arrays must have the same element type.
The direct Wasm compiler previously rejected these native-valid conversions.
The parent is `671f86b2406eaf9e32f9e08e99d3404d032dc1a9`.

The candidate compiler SHA256 is
`875bd697037a63c2dc20d9b9dd7d06f2135b81b43adcdde402c59b467153e70a`.
The build source hashes and immutable executable identity are in the archive.
The final snapshot includes 85 source files. Its seven runtime files beyond
the original 78-file inventory also match the parent commit. The first final
verifier stopped on that inventory difference; its failure and helper remain
preserved. The corrected verifier checks all 85 files.

## Lowering

`CanCopyLimitedArray` admits only two resolved `A_LIMITED` layouts with the same
element type and different capacities. Exact-layout copies keep their old path.
The existing fixed-source adapter remains separate.

`CopyLimitedArray` reads the source length once, after source evaluation. If the
source capacity exceeds the destination capacity, it checks the active length
against the destination limit. A failure occurs before payload or length writes.
Otherwise the source layout already proves that its length fits.

The copy uses each layout's own length-field size and copies only the active
payload. Its byte count is the active length times the element size. Both whole
layouts must fit memory32, so a valid source count cannot overflow that byte
count. The destination count is written after the payload copy. The original
captured destination and its memory identity remain in use throughout.

This path is shared by declarations, fields, assignment, by-value parameters,
results, inline calls and callbacks. A mismatched call result first uses its
own declared source layout in the existing checked temporary. Conversion then
uses that temporary. A stored source needs no extra owner allocation. The new
code uses two Wasm locals for the count and byte count. Copy work grows with the
active payload, as required to produce an independent value. No measurement or
performance acceptance was run, per the owner's correctness-only directive.

## Failing-first evidence

The preserved parent compiler accepts and executes all 32 final fixture
families in native code. It rejects the same sources on the Wasm target with a
pending-destination diagnostic. Each source hash and native result is checked
against its committed fixture and expected output.

The families cover widening, shrinking, ordinary references, assignments,
Memory 0 and data-memory fields, recursive and inline results, callbacks,
parameter snapshots, source length changes, reference elements, padded structs,
empty arrays and lengths 256 and 65536. Separate tests cover reference rebinding
during the right-hand expression and calls with dynamic source/destination
memory identities.

Five initial fixture attempts were invalid: a joined `&=` token, two uninitialized
arrays and two loop-syntax errors. The additional wide attempts retained the
same loop error. They are preserved and excluded from the 32 failures. The
final empty arrays have explicit initializers; the wide loops use valid Goose
syntax. `parent-verification.json` lists the exact attempts rather than counting
them as production defects.

## Observers and controls

All 32 families run at `-O0` and `-O2` in native code, Node and Wasmtime. Completed
owner checks inspect each scoped memory stack after `_start` returns. They also
check host completion state.

The Memory 0 observer copies padded elements. It gives active source padding,
unused source capacity, unused destination capacity and an adjacent sentinel
different byte patterns. It checks the entire memory image and both live and
completed frame tops. Controls shorten or extend the copy, change the count and
remove frame restoration.

The data observer constructs a limited field in a new data array from a field
in another data memory. The source passes through a reference-returning call.
It checks both full data images and Memory 0, live data tops, completed cleanup,
unused target capacity and the trailing field. Controls change the copy size,
the count store width and its memory identity.

The wide observer checks a 256-element source with a 16-bit count, a destination
with a 32-bit count and a second conversion back to a 16-bit count. It poisons
both destinations before conversion and checks full images after each copy.
Controls change each length store width or suppress the payload copy.

The failure observer runs a source producer that increments a global counter
and changes one existing destination element, then returns four elements for
a three-element destination. Native failure instrumentation verifies those
source effects and the unchanged destination length and other elements. Node
checks the complete published image after the capacity failure. Wasmtime checks
the same output and failure reason. A valid inverted-capacity-guard control must
fail the observer. The failed instance retains the private checked source
reservation and cannot run again. This is not a terminal-unwind cleanup claim.

The initial guard used error code 9, which means "pop from empty array".
The first loose message test also matched "capacity" in the source filename
and missed that error. A separate exact-message regression failed on the saved
first compiler. The corrected guard uses code 10 and both hosts must report
"array capacity exceeded" before the source path. The old source, assertions,
failing exact check and interrupted obsolete full suite remain preserved.
The new compiler is rebuilt from a new source snapshot, and its complete
correctness checks run separately.

The focused helpers contribute 32 observer/control checks: 20 payload/data,
8 wide-length and 4 failure/control checks. Damaged modules are parsed and
validated before they execute. The old limited-capacity and reference-capacity
admission tests now require successful native/Node/Wasmtime behavior.

## Full validation

Final source, test, compiler and archived-file verification is recorded in
[`limited-array-layout/final-validation.json`](limited-array-layout/final-validation.json).
It gives the actual full Wasm, native baseline, exact comparison and unchanged
module counts. The archive retains subprocess commands, stdout, stderr, exit
statuses, source hashes and the corrected invalid fixture attempts.

No timing, measurement lease, performance sample or JIT-sweep handback is part
of this work. Variable/growable arrays, data-array prefix conversion, slices and
conversions between different element types remain separate work.
