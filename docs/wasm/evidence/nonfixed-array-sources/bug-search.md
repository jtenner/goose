# Stored nonfixed source review

Scope supplied by the parent: `feat/wasm-multimemory-backend`, stated HEAD
`06ba2c50`, with frozen aggregate-prefix and unused-slot changes. Reviewed the
proposed `/tmp/goose-wasm-nonfixed-source-20261108/proposed-wasm_arrays.h` diff
against current `src/wasm_arrays.h` and the source paths named below. No source
edits, builds, tests, guest runs, timing, profiling, lease commands, status
polling, or child agents were used. This is a source-only review, not proof that
the proposed compiler executes the cases correctly.

## Result

No confirmed defect for valid inputs was found in the proposed classifier
extension. In particular, the suggested plain/global growable owner
`NoLocal` failure does not follow the actual conversion path.

## Address and memory identity checks

1. Proposed lines 397-403 call `ArrayFromPlace` on the `FixedPlace` selected by
   `WithReadPlace`. For a direct growable `Ident`, `ResolvePlace` takes its
   `OwnerPlace` branch (`src/wasm_fixed.h:440-449`). `OwnerPlace` always allocates
   an I32 local, calls `Address(slot)`, and stores the result in that local
   (`src/wasm_fixed.h:50-54`). `Address` emits a constant for globals and the
   frame address for locals (`src/wasm_codegen.h:372-375`). Thus, both
   `LoadArrayField` and `ElementOffset` receive a real address local. Their
   `code.Get(image.address)` calls do not receive `NoLocal` on this path.

   `FrameArrayOwner` can construct an image with `NoLocal` for a global,
   but also sets `ownerSlot` (`src/wasm_arrays.h:46-50`). Both field reads and
   growable payload address reads use `Address(*ownerSlot)` when it is set
   (`src/wasm_arrays.h:157`, `1022`). No fix for this suspected issue is needed.

2. `ArrayFromPlace` requires growable headers to be unpacked Memory 0 places
   and sets `elementMemory=-1` (`src/wasm_arrays.h:28-34`). It does not confuse
   the header memory with payload memory. At element index zero,
   `ElementOffset` loads the full I64 payload pointer from header offset zero
   (`src/wasm_arrays.h:1021-1023`), preserves its upper memory identity, and
   checks low-offset arithmetic (`1034-1048`). The proposed conversion retains
   `elementMemory=-1` in its captured payload `FixedPlace` (proposed line 403),
   so `CopyBytes` uses packed source dispatch (`src/wasm_arrays.h:251-266`).
   The proposal does not refine growable payloads to header Memory 0.

3. For a direct runtime-limited owner, `ResolvePlace` loads its packed data
   pointer and records the storage plan's concrete memory, or `-1` for a
   dynamic namespace (`src/wasm_fixed.h:446-448`). For a borrowed reference,
   `PointeePlace` preserves an I64 packed pointer and records memory `-1`
   (`src/wasm_fixed.h:424-431`). `LoadArrayField`, `ElementOffset`, and
   `CopyBytes` retain these representations. A runtime-limited reference
   returned from a call takes `Gen(n, actual)` once and then `PointeePlace`
   (`src/wasm_fixed.h:455-461`). Growable references use the existing thin
   header ABI (`src/wasm_codegen.h:142-148`).

## Length, capacity, and copy checks

* Runtime-limited data layout is U32 capacity at offset 0, U32 active length at
  offset 4, and elements at offset 8 (`src/value_layout.h:34-41`). Proposed
  line 399 captures active length through `ArrayLength`, and line 402 obtains
  payload offset 8 through `ElementOffset`. It does not copy the capacity
  word as length or include unused capacity in the payload.
* Proposed lines 462-465 set a runtime-limited receiver's capacity and length
  to captured active length. Exact-layout sources are excluded by line 378
  and remain on `InitArrayCopy`, which reads source capacity for exact
  runtime-limited copies (`src/wasm_arrays.h:503-509`). The two behaviors are
  separate in source.
* Receiving narrow prefix guards are before allocation (proposed lines
  417-419). The unsigned payload product guard is at lines 424-426; the prefix
  sum guard is at lines 428-430. Empty growable sources still have a packed
  payload pointer initialized with their own memory identity and saved top
  (`src/wasm_arrays.h:939-956`); a zero-byte copy does not require an element
  read. Varint receiving prefix calculation is bounded by the U64 count width.

## Evaluation, cleanup, and admission checks

* Source selection, reference null checks, active length, and payload address
  occur before receiving allocation (proposed lines 392-403 versus 432-438).
  No guest callback or source evaluation occurs between length capture and
  payload capture. A reference call is evaluated once by `ResolvePlace`.
  Index/field paths use the `WithReadPlace` callback protocol, which keeps a
  fixed parent temporary alive until the copy consumer returns
  (`src/wasm_fixed.h:516-550`, `139-157`).
* The receiver restore is registered in its declaration scope at proposed
  lines 387-390 and 439-440. The source path for newly admitted growable or
  runtime-limited values does not create a fixed temporary scope of its own.
  Dynamic receiver identity is captured before registration. Existing cleanup
  restores in reverse order (`src/wasm_codegen.h:453-464`). No new cleanup
  ordering defect was found.
* Nonfixed block/conditional values remain outside admission through
  `FindFixedArraySource` (`src/wasm_fixed.h:31-47`). General array-returning
  calls remain rejected by `ResolvePlace` unless they return a reference
  (`src/wasm_fixed.h:455-458`). Existing type admission still rejects direct
  references to growable owners as array elements
  (`src/wasm_support.h:19-22`, `src/wasm_codegen.h:219-220`). Runtime-limited
  owner references remain scalar reference elements. No admission change is
  required for the proposed extension.

## Unexecuted controls and limits

These are recommended checks, not confirmed defects:

* Direct global and local growable sources to variable, LEB, and runtime-limited
  receivers. Include `A_GROW` and `A_GROWSHRINK`, empty/default sources, and
  a popped source. Assert copied content and source independence.
* A runtime-limited source with capacity greater than length, and the same
  source reached through a reference element, a reference field, and a
  reference-returning call with a counter and source mutation. Assert one
  source call, active payload only, and receiving runtime capacity equal to
  length. Also retain exact-layout capacity-copy checks.
* Recursive calls with dynamic storage namespaces and repeated loop scopes.
  Assert receiver and source storage state only after completion signals, as
  required by the standing resource-test rules.
* Damage controls need to distinguish dynamic pointers from direct planned
  owners. A direct runtime-limited owner's known `image.memory` means field
  reads and copies use the plan's memory after truncating its packed pointer
  (`src/wasm_fixed.h:448`; `src/wasm_arrays.h:161-163`, `254-257`). Changing only
  the packed pointer's upper memory bits need not trap for that owner. This
  is existing behavior for stored variable owners too, not a valid-input
  defect introduced by the proposal. Borrowed runtime-limited references
  and growable payloads retain dynamic identity and reach dispatcher checks.
* No runtime, benchmark, allocation, or code-size result was produced. New
  conversions use the existing checked copy path with constant capture work
  plus a payload copy proportional to active payload bytes. This statement
  describes source structure, not measured performance.

Read evidence: `plan.md`; complete proposed conversion diff; parent01 four
Goose fixtures, `results.json`, and `checks.py`; the relevant array layout,
place, storage plan, memory helper, scalar element policy, fixed temporary,
and cleanup source paths; existing variable-prefix reference, indexed
reference, field reference, dynamic-memory, runtime-limited, packed ABI,
copy, and array-place test source.

Unread or unverified: full repository source, complete full-suite fixtures,
generated parent C files, parent binaries, every raw subprocess log, every
proposed positive/control case, and the active full-suite results. The parent
results table records four native passes and four Wasm compile rejections;
those cases were not rerun. No claim of executable correctness or test
completion is made here.
