# Fork-only raw address atomics

Owner ruling: Joshua, 2026-10-30. This deliberately unsafe facility belongs
only to the jtenner fork; do not propose it upstream. The safer capability
work remains separate. No capability type, registration or access check was
weakened.

The API is `unsafe_atomic_{load,store,fetch_add,compare_exchange}<T>` over a
`u64` address and `unsafe_atomic_is_lock_free<T>()`, with exactly one type
argument, `u32` or `u64`. Compare-exchange returns observed value then success
and is strong. See [native memory](../native_memory.md#fork-only-unsafe-raw-address-atomics)
for exact contracts and a Slipstream adoption example.

## Implementation and tests

The typechecker normalizes the raw operation to the corresponding existing
atomic operation before running the existing order validation. Native C uses
GCC/Clang `__atomic_*`, static assertions of always-lock-free width, and an
address guard before pointer construction and access. Every non-order operand
is snapshotted once in evaluation order. TinyCC and MSVC are explicitly
rejected. Raw operations neither construct nor inspect shared capabilities.
The opt-in strict worker-native contract retains its unsafe-operation ban.
Atomic operations invalidate optimizer bounds/storage facts, including through
non-inlined callers, matching capability synchronization and unsafe stores.

The initial fixtures were committed before implementation and rejected by the
pre-change compiler with unknown builtin diagnostics (`evidence/red.log`).
`test/unsafe_atomics.py` exhausts all five orders for both widths for load,
store, add and every success/failure CAS pair; it checks generated C, strong
CAS, unsupported backends, forced non-lock-free rejection, exact diagnostic
on misalignment, type/address rejection and strict worker rejection.
`test/memory/unsafe_atomics.goose` repeats 16-worker claims ten times (eight
workers per width, 10,000 increments each), checks exact 80,000 totals, both
CAS outcomes, unsigned wraparound, and all four misaligned operations at both
widths. `raw_atomic_publication.goose` verifies that synchronized raw writes
cannot leave stale safe-index bounds assumptions.

## Validation results

Results and toolchain details are recorded here after full validation.
