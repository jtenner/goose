# Read-only source bug search

Worker limited_constructor_bug_search inspected the new constructor and helpers.
No builds, guests, measurements or edits ran in the worker.

Confirmed defect: LenStore requires resolved static capacity. Calling it for a
runtime-limited target asserts with assertions on, or selects u8 for capacity -1
with assertions off. A valid count 256 then gets the wrong prefix-range error.
Use ArrayPrefix(array->arr).storage at the width lookup. Verify runtime target
length, capacity and payload at 256. Keep the old candidate and failure.

No other concrete error found in LEB encoding, memory identity, source effects
or cleanup scope. Add u8 prefix boundary 255/256 checks.
