# Direct WebAssembly backend

This project starts at upstream/master
`7b90f91d91845f4ef1712e16ed053f395e4e6e1c`. It does not use generated C as
an intermediate representation. The default C backend must keep its current
behavior. This document describes the target ABI and the implementation gates;
it does not claim that all gates are complete.

The implemented path is scalar code with Memory 0 frames and a Node adapter.
The complete multi-memory Goose backend is unfinished. Encoder tests with
multiple memories do not establish Goose data-stack assignment.

## Frontend and storage analysis

Parsing, resolution, specialization, root/lifetime checking, optimization, and
bounds-check elimination remain the existing frontend passes. Lower the checked
`FnSpec::body`, including optimizer-created `InlineBlock` and `LoopExpr` nodes.
Variable and return-target identities are AST object identities, not names.

The current C backend collects stack counts while it emits C. `AllocStk`,
`SaveBase`, `NoteStackCall`, and scope exit are not independent AST passes.
`BoundStacks` can solve a symbolic call graph, but does not collect that graph.
Likewise `FixedSize`, `LayoutFields`, and frame-object prefix calculations live
inside `CodeGen`. A backend must not construct `CodeGen` and discard its C to
obtain these results. The layout and stack services need a separate extraction
before general compound-value lowering. Lifetime classes constrain storage;
they are not physical stack identities.

The storage plan must record slots, ordered scope saves/deferred bodies, call
watermarks, temporary owners, protected result destinations, and logical stack
indices before instruction emission. Each physical memory corresponds to one
logical data stack. A backend function variant binds its specialization's local
stack base, reference memory identities, captures, and result destinations.
Recursive edges must satisfy the existing no-live-local-stack restriction.
A finite variant budget must retain dynamic dispatch as its fallback.

## Memory32 ABI

Memory 0 holds static bytes, persistent globals, host exchange buffers, and
addressable activation frames. Memory 1 and later hold assigned Goose data
stacks. Stack assignment follows overlapping lifetimes, not element types.
No fixed partitions, moving heaps, WasmGC values, or custom execution stack are
part of this target.

Known-memory addresses are i32 byte offsets. Dynamic addresses are i64 values:
`(u64(memory_index) << 32) | u32(offset)`. Zero is null. Reserve the first byte
of each memory so that zero cannot identify live storage. Address arithmetic
must check its offset before packing; overflow must never change memory identity.
Dynamic accesses must validate the memory identity and dispatch to instructions
with concrete memory indices. Preserve provenance through derivations and calls.

Thin i32 pointers are an SSA/call optimization only. Stored ordinary reference
fields use an 8-byte packed address, slices use an 8-byte address followed by an
8-byte count, and resizable owner references use an 8-byte header address and
an 8-byte element-stack identity. Pool descriptors add 8-byte freelist address
and 8-byte freelist-stack identity fields. Relative fields retain their declared
widths. No variant may alter a value's stored layout.

Pointer representation is compiler-private. Serialized relative references keep
their declared widths and origins. Slices retain their counts. Resizable owner
references retain both the address of the owner header and the element stack
identity. Pool references also need freelist descriptors. One packed address
cannot replace all of these descriptors.

Memory 0 has a persistent static/global prefix followed by transient frames.
Frame restores cannot release the persistent prefix or caller-owned storage.
All growth and page rounding use i64 arithmetic. The initial frame top is i32,
so its explicit exclusive-top limit is UINT32_MAX, one byte below 4 GiB. Check
that limit before narrowing or writing. The initial adapter permits one `_start`
per instance and no host callback into guest code. Exchange byte ranges are
borrowed only during the import; the host copies rendered bytes before return.

Scalars use i64 for Goose integer computation, i32 for bool, f32/f64 for floats.
Narrow integer results are normalized at the operation's declared width before
conversion to a wider receiving type. Signed remainder is Euclidean. Shifts mask
by the Goose width. Floating conversions must implement Goose wrapping and
NaN rules rather than use trapping or saturating Wasm conversion alone.

Address-taken scalar storage is authoritative in Memory 0. Other scalar locals
remain Wasm locals. Frames use ordinary Wasm calls and recursion; frame growth
must succeed before stores occur. Restore the frame watermark at each ordinary
or exceptional function exit. Traps abort the instance and do not run defers.

Packed aggregate fields, explicit pads, array length widths, varints, ADT tags,
resizable tails, and byte-view semantics must retain the specification's layout.
Use unaligned scalar operations with conservative alignment hints. A resizable
owner header remains two scalar 64-bit fields where the existing representation
requires that form. Do not introduce SIMD headers.

## Control and results

Use structured block/loop/if branches and ordinary calls. Return values must be
selected before cleanup. Inline return targets branch to their enclosing inline
exit with no exception metadata. A remaining nonlocal call boundary requires
`tag`, `throw`, `try_table`, and exact resolved target identity. Recursive target
calls catch at the innermost matching activation.

Cleanup must interleave reverse-ordered watermark restores and reached deferred
bodies at their registration points. Direct construction and named-result landing
must protect an in-flight result from intermediate restores. Extract the existing
`LandValue` behavior rather than replace it with unconditional temporary copies.

## Initial host contract

Use versioned `goose` imports and export Memory 0 as `memory`. Byte arguments to
the host are Memory 0 offsets and counts. Other memories require adapters.
A print operation collects rendered pieces before one output write, including
nested calls that print during argument evaluation. Native externs and workers
need explicit adapters; unsupported facilities must produce a target diagnostic.
Worker adapters must use independent instances and copy flat message bytes.
Raw guest references cannot cross worker instances. A future worker adapter
must also copy the used mutable-global snapshot and reconstruct permitted
static-data references against the destination instance's static symbols.

The module emitter writes standard binary sections directly. It needs no C
compiler, LLVM, external assembler, or third-party encoder at compile time.
Validate emitted modules independently with `wasm-tools`.

## Runtime probes

On 2026-11-06, a module using two memories, an unaligned scalar store/load in
Memory 1, and `try_table`/`throw` returned 42 under both:

- Node.js 24.22.2, V8 13.6.233.17-node.63.
- Wasmtime 49.0.3, with multi-memory and exceptions enabled.

The probe was assembled and validated by wasm-tools 1.262.0. This checks engine
capability, not compiler implementation or language coverage.

Encoding references: [Wasm binary instructions](https://webassembly.github.io/spec/core/binary/instructions.html),
[multi-memory encoding](https://github.com/WebAssembly/spec/blob/main/proposals/multi-memory/Overview.md),
and [Wasmtime configuration](https://docs.wasmtime.dev/api/wasmtime/struct.Config.html).

## Stage gates

A: record a clean upstream native baseline and independent ABI review.
B: direct scalar modules, calls, control, locals, checked frame storage, and
   differential tests under a real engine.
C: storage plan, one memory per logical data stack, checked growth, and thin/fat
   reference dispatch with stable offsets.
D: shared layout authority, every value class, root/relative descriptors, and
   byte-for-byte serialization tests.
E: direct placement, named-result landing, ordered cleanup, and both nonlocal
   return paths.
F: host services, globals, native adapters, isolated workers, and queues.
G: bounded specialization, dispatch/growth hoisting, measurements, and full
   differential/native validation.

Do not claim the complete backend until all gates pass. Unsupported features in
earlier gates must fail explicitly before an output module is written.

## Upstream baseline

The Release build and native baseline passed before driver integration on
2026-11-06. Command: `mise exec clang@23.1.3 -- python3 test/run_tests.py
--profile baseline --cc native --require-clang --exe build/goose`. The host has
`python3`, not `python`. Compiler SHA256:
`689948f57a25ff501ee8400428e11680981e9584b6c286fbc029afaf157e24a9`.
Audio, gfx, and UI layers/devices were unavailable; the runner reported its
skips. Physics was built in. The sample portion reported 52 passing checks.
The preliminary fork baseline was stopped when the user changed the base; it
is not the upstream baseline.

## Encoder reference

The nearby `starshine-mb` checkout, revision
`b28144a7c50f1dc360825f7f68220022101b9921`, was inspected after the initial
encoder worked. Its `src/binary/encode.mbt`, `encode_control.mbt`, and LEB and
memory-argument boundary tests informed additional checks for u32 field limits
and multi-byte memory-index/offset order. No Starshine source was copied.
The Goose writer uses the same standard `flags, memory index, offset` order.
Its emitted memories use Memory32; unsigned module fields are bounded to u32.
Future EH emission must respect tag-section placement before globals, rather
than order sections solely by their numeric IDs.

Reference: [Starshine encoder](https://github.com/jtenner/starshine-mb/blob/b28144a7c50f1dc360825f7f68220022101b9921/src/binary/encode.mbt).

## Current checkpoint

The complete project is still unfinished. The tested scalar path, exact source
and binary identities, independent review records, measured converter change,
and remaining stages are recorded in [the status report](../wasm/status.md).
