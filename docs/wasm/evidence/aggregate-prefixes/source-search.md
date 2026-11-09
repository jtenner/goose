# Read-only source bug search

Native GPT-6.1-Sol high worker inspected fixed-prefix aggregate paths. It made
no edits and ran no build, guest, timing or lease command. No additional
four-byte offset was found in fresh children, nested arrays, copies, reference
access or ArrayFor. Source offsets remain layout-based. Aggregate equality is
still gated. Parser admits u8/u16/u32/u64/varint length storage only.

The worker identified an existing compile-time rejection for a known oversized
fixed source in InitFixedArrayValue, separate from ReserveFreshDataArray.
This is a limit, not a confirmed production defect. Scalar literal construction
has the same compile-time prefix-range policy. The proposed aggregate literal
path retains that policy. Exact-copy count width is already proved by the source
layout equality and unsigned count load; the existing byte-size check remains.

Wide-count-elements expectations in struct/enum admission tests need updates.
Required tests include fixed/limited child arrays, copied binders, references,
exact copies and complete memory images. Worker test sketches are not runtime
evidence. Native parent results are saved separately.

## Unused-slot follow-up

The read-only worker checked fresh-construction paths after a valid retained
slot reference reproduced a stale value. It found the same suffix issue in
limited-array defaults and fills. Empty nominal defaults must not call inactive
element defaults; zero-count fills must still evaluate their fill value once.
Stored whole-value copies must preserve source spare bytes. These cases are
covered by the separately recorded failing-first programs and final fixtures.
The worker ran no commands that compile or execute Goose guests.
