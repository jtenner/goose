# Runtime-capacity limited arrays

The admitted scalar/ordinary-reference array subset now includes `T[..]`.
`[..capacity]` evaluates capacity once, checks its unsigned u32 range, checks
prefix plus capacity times element stride against Memory32, and reserves the
whole region before publishing the owner and metadata. The packed value is
u32 capacity, u32 length, then elements. An explicit literal, fill or string
chooses its initial length as capacity. General copies/assignments, by-value
parameters/results, compound/relative layouts and varints remain pending.

`ValueLayout::ArrayPrefix` owns the packed offsets. Native C construction/view
paths and Wasm field operations use those offsets; `LenStore` retains its
previous contract. Static limited arrays remain inline in Memory0. Runtime
limited owners use data memory with a private local/global pointer slot.
References denote the packed header, not that private slot. Capacity stays
reserved while push/pop/clear update length. Calls, aliases, equality, mutable
iteration paths, globals and ordered defer/scope restoration use existing rules.

Dynamic access helpers now include a full u32 field offset in a u64 cache key.
Offsets remain memory-instruction immediates and cannot carry into the packed
memory id. Tests distinguish offset 0, offset 4 and offset 16777216, including bounds
and unsigned values. Old zero-offset helper names and bytes remain unchanged.

Release compiler SHA256:
`fbbf0e36f41b37614c9b1f48e7f61502c0ae215b44ea6710eaa212d9b5bd9389`.
Four native-valid inputs first ran at O0/O2 on the prior compiler. Its Wasm
backend rejected their specific unsupported layout and wrote no module. New
O0/O2 modules validate with wasm-tools 1.262.0 and match native in Node 24.22.2
and Wasmtime Python 49.0.0. Actual owner tops are checked after `_start`.
Cases cover dynamic allocation/call bases, capacity versus length, reference
parameters/results/elements, visible path rebinding, float/bool/fill/string
values, different capacities with equal values, global storage, 10,000 scoped
reuses, clear/pop/push, successful growth, nullable/no-owner interfaces and
normal/return/break/continue/defer cleanup.

The reviewed full suite passed 375 checks. The fresh full native baseline
passed with its recorded device/platform/unsupported-JIT skips. All 52 exact
older-checkpoint artifact/diagnostic comparisons and 76 immediate-prior Wasm
module pairs match. Native C outputs for the new cases also match the prior
compiler after source-path normalization in review. Source and adapters were
frozen for this build/run. All children were reaped, owner 3638752 exited, the
lease was released and a fresh exclusive nonblocking probe passed and was
immediately released. Raw evidence is `/tmp/goose-wasm-runtime-limited-20261107`;
the [release record](runtime-limited/release-verification.json) pins provenance.

The independent [Astra review](runtime-limited/astra-review.md) found no
confirmed correctness or design defect. It identified two weak test
expectations. A test-only follow-up now uses index 1 with length 1 and capacity 2 and
checks the exact invalid-capacity reason for each backend. All six O0/O2 cases
passed with the same preserved compiler. A derived, validated module changes
only the index check's field from length to capacity; it returns `bad=0` in
both engines and fails the stronger expectation. Specific stdout/stderr/status
and control identity are retained in [review-checks](runtime-limited/review-checks/results.json).
No production code or compiler binary changed after review. The full 375 record
uses the reviewed harness; the later focused run verifies the tightened rows.

The byte-count overflow test validates native source but does not attempt a
multi-gigabyte native allocation. The target checks it before reservation;
actual data tops remain 1 and buffers remain one page after the completed
exception. The separate helper test forces a real growth failure. Neither
proves general stack unwinding on terminal failure. Host print-buffer counts
read after terminal cleanup are not proof of guest release; the separate
byte-snapshot harness supplies active-owner observations for its own cases.

Saved module size ranges: values 15,049 to 15,299 bytes; bytes 8,168 to 8,182;
cleanup 8,329 to 11,345; no_owner 1,034 to 1,057. Their memory counts are 11, 6, 6, 1,
respectively. Each memory starts at 64 KiB. Capacity-only construction uses fixed
bookkeeping, with guest reservation `8 + capacity * stride`; it does not emit
per-capacity-element initialization. Engine growth may still scale with capacity.
The cache's wider key can increase compiler map-node size. Conservative lexical
ownership and per-memory page rounding can retain more address space than live
values need. Resetting a top does not shrink a buffer or prove physical release.

No controlled runtime/compiler CPU/RSS, allocation, process-residency or
cross-platform measurements were taken. Linux x86-64 is the only execution
evidence. No speed gain or minimal memory claim is made. Queued coordinated
work includes common compile paths, offset dispatch, runtime capacities,
initializer-call depth, many owners and high-water retention, with the exact
prior/native identities and the shared measurement lease. It remains part of
the project's required performance matrix, not an extension of a closed grant.
The report retains further gaps for default construction, u64 capacity extremes,
zero-count effectful fills and large explicit runtime-limited literals.
