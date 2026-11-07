# Initial Wasm data-stack path

This stage adds separate data memories for explicit growable scalar-array
owners. It is part of the backend implementation, not completion of the full
multi-memory project. The checked frontend, ownership rules, C emission, and
native runtime remain unchanged.

## Storage and access

`WasmStoragePlan` collects lexical owner indices and call watermarks before
emission. It uses the shared call-bound solver. Overlapping owners, including
owners with the same element type, receive separate memories. Disjoint scopes
reuse logical indices. Global owners have persistent dedicated memories.
A function has a constant memory base when every incoming path agrees;
otherwise it receives one hidden i32 base. The propagation worklist permits at
most two state changes per function. Recursive edges keep the existing
no-live-local-stack restriction. More than 64 data memories produces a target
diagnostic before output; memories are not merged to bypass that limit.

Memory 0 holds authoritative array headers and address-taken frame slots.
Data memories start at offset 1. Each has its own top. Reservations check the
exclusive end with i64 arithmetic, grow before writing or publishing the top,
and preserve offsets. Known memories use fixed-index instructions. Packed
references use high-u32 memory and low-u32 offset, with shared checked
`br_table` access helpers. Unknown owner bases use analogous reservation and
top dispatch. Scope cleanup records watermark restores and defers in one
ordered list and executes it in reverse registration order.

All stored ordinary references retain 8 bytes. Stored owner references retain
16 bytes. Since every currently admitted owner header is in Memory 0, its SSA
reference is an i32 header address; its growth identity is recovered from the
immutable initialized header base. Compound owners and arrays of owner
references remain rejected until their descriptor lowering exists.

## Regression evidence

Failing-first checks are preserved outside the source tree under
`/tmp/goose-wasm-multimemory-20261107` and
`/tmp/goose-wasm-entry-call-20261107`:

- A bare optional null reached an unsupported placeholder type. The same
  native-valid case now uses the target's zero reference representation.
- By-reference iteration over reference elements bound the element slot
  instead of its pointee. Native output changed the pointees; Wasm did not.
  Optional and nonoptional element fixtures now exercise the pointee load.
- A mutable array-reference iterator retained its first header after rebinding.
  The regression now rereads that reference at each loop test, as native does.
- A live array-reference interface with no actual data owner emitted invalid
  reference types. Reference representation now follows live interface types,
  independently of the physical memory count.
- A native-valid array-valued temporary produced 99 instead of 7 after its
  data stack was restored too early. Such call, block, and branch temporaries
  now receive a specific destination-lowering diagnostic before output.
  Full destination construction is still pending.
- Calling `main` from a global initializer with a live array made its entry
  base dynamic. O0 emitted an invalid module because `_start` omitted the
  hidden i32 argument. The native result is two lines containing 7. The entry
  call now supplies base 0 when required. O0 and O2 are permanent fixtures.

Invalid source drafts are not counted as regression coverage. Forward global
references are already rejected by the frontend; no initialization-order
change was made.

## Validation and measurement limits

The pre-entry-fix Release compiler SHA256 was
`959d31ea4949ae52f74e09e5ea5c8445036e8e928f3f4375b91c4c911c19e2c5`.
It passed 157 Wasm checks and the full native baseline suite. A previous run of
the same compiler passed all 52 saved native/scalar output comparisons.
The entry-fix Release compiler SHA256 is
`8ee9634cd097905e2e73aa56a57148b3e38cfe57e62f6fc199fc84104479d247`.
It passed 163 Wasm checks. The same native-valid entry-call source now validates
and produces the expected output at O0/O2 under Node and Wasmtime. The full native baseline suite and all 52 exact native/scalar comparisons also
passed. Astra's independent read-only review found no confirmed new defect in all 38
changed files of its frozen packet. The packet predated this final validation.
The subsequent Release run resolves its exact-candidate validation gap. A
separate native/Node/Wasmtime O0/O2 cleanup fixture resolves the exit-path
coverage gap: reached defers interleave with owners on normal exit, return,
break and continue; deferred bodies allocate and call a function reached at
multiple stack bases. All scoped tops are restored at completion. That fixture
and its small harness registration were added after review. No core source
changed after the reviewed snapshot.

Independent runtime-helper checks cover all admitted scalar widths, signed
loads, unaligned addresses, stable references across growth, separate memory
growth, invalid identities, overflow, real grow failure, unchanged top after
failure, and saved-top validation. Language fixtures compare native, Node,
and Wasmtime output at O0/O2. Completion checks observe the owner's state
after `_start` returns, not after a delay. Separate same-type owners grow to
at least two pages each. Twenty scopes with 9,000 pushes each reuse the same
two-page data memory. Eleven scalar/reference element types reuse one logical
memory across disjoint scopes. A separate maximum-boundary check compiled
64 live owners into exactly 65 memories including Memory 0. Native output,
Node and Wasmtime O0/O2 execution, and completed stack-top checks pass. The
65-owner case is rejected for the documented backend limit before output.
Raw commands, stdout/stderr, exits, identities, and lease verification are in
[the evidence directory](data-stacks), including [the boundary unit](data-stacks/limit64.json).

These are addressable-memory and stack-state checks. They are not physical
RSS, allocation-count, or compiler-cost measurements. No new performance
samples have been acquired. The previous scalar comparison modules remain
byte-identical. Array reference paths and dispatch add new runtime work, and
known array accesses still construct an intermediate packed address before
using a fixed-index load/store. General thin-reference propagation, bounded
loop specialization, growth hoisting, and the requested dispatch benchmark
matrix remain queued for a coordinated measurement turn. No array performance
gain is claimed against a prior backend that could not compile these inputs.

Every build/test unit held the shared lock nonblocking and released it after
all owned children were reaped. Source edits proceeded while Slipstream held
its own turns. No timing grant or sample budget was reused.


The retained [review](data-stacks/astra-review.md) describes the evidence
available to the reviewer, including missing individual comparison artifacts
in that packet. The later [validation records](data-stacks/validation-records.json),
[52-comparison summary](data-stacks/compatibility-summary.json),
[source manifest](data-stacks/source-manifest.json),
[snapshot verification](data-stacks/review-snapshot-verification.json), and
[cleanup records](data-stacks/cleanup.json) preserve the subsequent checks.
The complete old and new executables and generated comparison files remain in
the raw directories. Compact JSON archives preserve copied text exactly;
original raw evidence was not changed. The review does not establish compiler
cost, native code size, or runtime performance for this stage.
