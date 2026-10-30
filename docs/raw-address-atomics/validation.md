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

Linux x86-64, GCC 14.2 and Clang 23.1.3. The compiler was built in Release
for baseline, and with Clang `-O1 -g -fsanitize=address,undefined
-fno-omit-frame-pointer -fno-sanitize-recover=all` for the sanitizer profile.
The host-target Clang wrappers are retained in `evidence/clang-host` and
`evidence/clangxx-host`; they avoid this installation's Conda default linker
configuration. The first sanitizer link failed against `/lib64/libm.so.6`;
reconfiguring with these wrappers fixed the toolchain without a source change.

- Baseline: **5,104 section checks verified**, versus 5,094 before this change.
  The full parallel invocation passed 5,102 and failed two benchmark checks
  due to shared-native benchmark-lock contention. A complete repeat reproduced
  those same two failures; inspection found declarations and compatibility
  are scheduled concurrently with the runner's other lock-using benchmarks.
  Sequential reruns passed declarations (43 internal checks) and compatibility
  (17). No unresolved baseline failure remains. The full invocations and rerun
  are retained separately; this is not represented as one zero-failure run.
- The first sanitizer run lacked a stack symbolizer, so the existing narrow
  third-party shader LSan suppressions could not match frames. Its complete
  log is retained compressed as `evidence/sanitize-no-symbolizer.log.gz`.
  Enabling `allow_addr2line=true:external_symbolizer_path=/usr/bin/addr2line`
  restores symbolized reports and the existing suppressions; leak detection
  remains enabled. That run also exposed a test-only Clang error-limit issue
  when simulating MSVC against the entire runtime header; backend guard tests
  now use preprocessing so they exercise the intended explicit `#error`.
- Sanitizer: **4,319 section checks verified**, versus 4,309 before this
  change. With host Clang and addr2line configured, the full invocation passed
  4,318 and only benchmark declarations failed from lock contention. The
  sequential instrumented-compiler rerun passed all 43 internal declaration
  checks (`evidence/sanitize-benchmark-rerun.log`). No unresolved sanitizer
  failure remains; the full invocation and rerun are retained separately.
- Focused raw-atomic contract: passed all 80 order cases across both widths,
  generated-C inspection, strong CAS and backend/width/type/strict rejection,
  and loud runtime misalignment diagnostics (`evidence/contract.log`).
- Raw-atomic publication: all nine combinations of Goose O0/O1/O2 with native
  GCC, Clang, and Clang ASan/UBSan preserve the safe bounds diagnostic. The
  focused sanitizer compile retains alignment instrumentation and reports no
  sanitizer failures (`evidence/publication.log`).
- The known four upstream failures required no changes and are absent from
  this fork's baseline.

Compiler SHA256s (embedded build versions can contain the earlier test
checkpoint plus `dirty`; these are the binaries used for final source checks):

```
4c3b7012c3c9b9ce6b311bab66f1b8c14d294a7d173fc8775a623648d7d09615  build/goose
6dc637e3effaf06873859e13cbcf3e7a73831c45d099a527af552d79c190022d  build-sanitize/goose
```

Commands:

```
PATH=/tmp/goose-raw-toolchain:$PATH python3 test/run_tests.py --exe build/goose --profile baseline --cc native --require-clang -j 16
PATH=/tmp/goose-raw-toolchain:$PATH python3 test/bench_declarations.py build/goose
PATH=/tmp/goose-raw-toolchain:$PATH python3 test/bench_compatibility.py build/goose
PATH=/tmp/goose-raw-toolchain:$PATH ASAN_OPTIONS=allow_addr2line=true:external_symbolizer_path=/usr/bin/addr2line:detect_leaks=1 python3 test/run_tests.py --exe build-sanitize/goose --profile sanitize --cc clang -j 16
PATH=/tmp/goose-raw-toolchain:$PATH ASAN_OPTIONS=allow_addr2line=true:external_symbolizer_path=/usr/bin/addr2line:detect_leaks=1 LSAN_OPTIONS=suppressions=$PWD/test/lsan.supp python3 test/bench_declarations.py build-sanitize/goose
```
