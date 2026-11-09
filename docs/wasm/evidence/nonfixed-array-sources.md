# Stored growable and runtime-limited array sources

Stored growable, grow-shrink and runtime-capacity limited arrays now construct
fresh nonfixed arrays with matching fixed scalar or ordinary-reference element
layouts. The receiving layout can use a different unsigned count prefix,
canonical unsigned LEB128, a growable owner or a runtime-capacity owner.
The parent is `af5cc6b8c9107560a6ad9de1e4e5dbd38b89fbba`.

The tested Release compiler SHA256 is
`b70378cc7c0be14cb0651ac2842a2f82273e9a86834a40e9b9bd692e531850d8`.
The frozen source, Release build, assertion-enabled build and compiler flags
are recorded with the evidence. No performance test or measurement lease is
part of this work.

## Narrow source change

`InitCountedArrayValue` now routes these sources through its existing nonfixed
read-place path. That path captures the source once, reads its active count,
and retains the payload memory identity. A growable header resides in Memory 0;
its packed payload address can refer to a separate data memory. A runtime
limited source has a capacity field, a length field and inline data payload.
Its capacity must not be used as the active count.

The existing prefix-range, element-product and total-extent checks run before
receiving allocation. The fresh runtime capacity is the active source length.
Only active payload bytes are copied. Source spare capacity is not copied.
Exact-layout copies keep the previous path, which preserves their capacity.
The source remains live until the copy ends, then existing scope cleanup
restores temporary owners in order.

No compiler field, descriptor, table, IR form, shared interface or general
value-call ABI is added. The change is confined to one Wasm-only function.
Copy work and receiving storage grow with active element count. This is
required for an independent fresh value and uses the existing reservation and
bulk-copy services. No new per-element compiler allocation is introduced.
Runtime cost, compiler cost, allocation totals and physical memory are not
measured.

## Failing-first and positive checks

Sixty-seven native-valid families fail the parent Wasm conversion check. They
cover nonempty and empty sources, all receiving fixed unsigned prefixes,
LEB128 count 128, stored references, reference fields in Memory 0 and data
memories, indexed runtime references, global owners, once-only calls, loops,
real recursion, grow-shrink sources, pop, FP and Boolean values, scalar widths
and ordinary reference elements. The recursive cases end the nonfixed local
scope before the recursive call, as the shared language rules require.

Two parent-supported runtime-copy families check exact and read-only copies
with capacity nine and active length two. Their fresh independent copies must
retain capacity nine. Together, the 69 positive families pass native, Node,
Wasmtime and completed-owner checks at O0/O2. The assertion-enabled compiler
emits the same 138 Wasm modules as the Release compiler and passes Node checks.

Four native-valid range-failure pairs use a 256-element source and a u8-prefix
receiver. Native execution reports its specific array-storage range error.
The parent cannot compile the conversion. Both Wasm adapters now report the
specific stored-prefix error before receiving allocation.

## Complete images and fault controls

The new helper set has 136 checks. Static images cover Memory 0 and complete
source and receiver memories, with dirty spare capacity, poisoned free bytes,
sentinels, live tops and completed tops. Empty and LEB128 cases retain full
image checks. A dynamic borrowed source is called twice while a caller owner
is live. The second receiver must use a different data memory without changing
the caller's poisoned free bytes. Cleanup and memory identities are observed
at each checkpoint.

Validated damaged modules change copy length, source memory, prefix width,
LEB continuation, cleanup, count-field selection or Memory 0 bytes. Each must
fail its specific image or state assertion. An omitted source restore is not
counted for an empty growable owner whose initial top already equals one.

Separate malformed-header checks exercise element-product and prefix-sum
overflow. These are controlled memory-corruption tests, not native-valid
language inputs. The healthy module must fail before allocation and preserve
the full expected images. Mutated guards must reach the designated later
assertion or the specified bulk-copy bounds trap. These checks do not claim
terminal-trap unwinding or reentry support.

A native-valid array of references to growable owners retains the existing
compound-element rejection at both optimization levels. It does not widen
aggregate or growable-owner reference-element admission.

## Preserved helper failures

The first recursive sketch violated shared frontend rules by keeping a
nonfixed owner live across recursion. Its source and failure remain. The
corrected positive uses a closed scope and a real recursive call.

The first focused runner stopped during helper insertion before running a
compiler. A later sum-guard mutation selected a subsequent index comparison
instead of the pre-copy sum guard. Its failure and original helper remain;
the corrected selector is bounded before the copy. No compiler change was
made for these setup errors, and no failed run is reported as a pass.

## Final correctness record

All 7,279 Wasm correctness checks passed. The final record verifies all 85
compiler source files and 5,967 test/script inputs. All 1,754 old fixture
modules are byte-identical, all 138 assertion-enabled pairs match Release,
and all 52 exact comparisons pass. Immutable identities and selected phase
results are recorded in
[the validation record](nonfixed-array-sources/final-validation.json).
Raw evidence remains under `/tmp/goose-wasm-nonfixed-source-20261108`.
The old fixture phase is reused only after 1,754 current modules are re-emitted
and match the executed parent modules byte for byte. The 138 new pairs have
fresh native, Node, Wasmtime and owner checks. The integrated continuation
verifies every fixture source and module hash, then runs the core runtime and
layout units and every later helper afresh. All 52 shared-backend exact output
and diagnostic comparisons also run on the current compiler.

This is correctness reuse, not a claim that all old native programs were
executed again. The preceding checkpoint passed the full native baseline.
This increment changes only the private Wasm constructor path, and the new
native differential programs run on the frozen current compiler.

## Remaining scope

Aggregate runtime/growable elements, general nonfixed fields and value calls,
nonfixed block/if value transport, aggregate LEB prefixes and data fills,
slices, relative references, pools and host/worker compilation remain separate.
The complete backend is not finished. Stage F scope remains an owner question.
