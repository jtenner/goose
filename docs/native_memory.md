# Native memory

Native memory is separate from Goose arrays, references and copied worker
globals. `SharedOwner`, `SharedView`, `SharedAccess`, `SharedAtomicU32` and
`SharedAtomicU64` are opaque compiler types. Safe Goose cannot construct their
fields, convert integers to them, serialize them, or send them through queues
or C signatures. Copying a capability copies its authority; it does not create
a second allocation or a second right to free storage.

## Allocate, borrow and close

```goose
let owner, ok = shared_alloc(4096);
assert(ok);
let view = shared_view(owner, 0, 4096);
let access = shared_borrow(view);
memory_write<u32>(access, 1, 1234, false);
assert(memory_read<u32>(access, 1, false) == 1234);
shared_release(access);
assert(shared_close(owner));
```

`shared_alloc(bytes)` returns an owner and a success flag. Zero size, sizes
outside the native address space and OS allocation failures return false and
an invalid owner. POSIX uses anonymous `mmap`; Windows uses `VirtualAlloc`.
The runtime never fills or eagerly touches the allocated byte range. OS demand
paging supplies initial zero bytes; physical-memory exhaustion on later page
fault follows the operating system's policy.

`shared_view(owner, offset, bytes)` checks the complete subrange.
`shared_size(owner|view|access)` reports its byte length as `u64`. No operation
uses unchecked `offset + size` arithmetic. A zero-length view is valid at the
end of an allocation.

Every ordinary load, store and copy requires a live `SharedAccess` returned by
`shared_borrow(view)`. A borrow authorizes the calling thread exclusively for
that byte range. Creating any overlapping borrow fails, including a second
borrow on the same thread. Disjoint ranges may be borrowed independently.
`shared_release(access)` ends the authorization and invalidates all copies of
that access capability. It is an error to read, write or release it afterward.
Release before waiting for another worker that needs an overlapping range.

`memory_read<T>(access, offset, big_endian)` and
`memory_write<T>(access, offset, value, big_endian)` support exactly
`i8/i16/i32/i64/u8/u16/u32/u64`. `false` selects little endian and `true` selects
big endian, independently of host byte order. The runtime copies scalar bits
with `memcpy`, so unaligned byte offsets are supported. Bounds and read-only
permissions are checked in every build. `memory_copy(dst, dst_offset, src,
src_offset, bytes)` validates both authorizations and permits overlap through
`memmove`.

Only the owner thread can close an allocation. `shared_close(owner)` returns
false if it is already closed, invalid, has live worker leases, or has active
borrows; a false result leaves a live allocation open. Successful close
unmaps once and invalidates every derived capability. A slot reused by a later
allocation has a new generation, so stale values never revive.

Worker arguments may explicitly include `SharedView` and shared atomic
capabilities. Owners and active accesses cannot cross worker boundaries.
Ordinary references, arrays and worker globals retain their existing isolation
rules. Leases are acquired before native worker creation and retained through
all worker execution. Normal return and a contained abort both release
abandoned borrows, owned allocations and worker leases before completion is
published. A worker-created allocation passed to a child is reclaimed only
after the last child's lease ends. Main normal return performs the same
context cleanup. Process-fatal exits rely on OS reclamation.

Capability value wrappers have byte alignment, so packed fields, arrays,
returns and worker packets never require an aligned wrapper address. Registry
descriptors and mapped atomic cells retain their natural alignment.

Capability records occupy stable reusable metadata slabs. Mapping storage is
released on close; the slabs retain generation tombstones and grow only with
peak simultaneous descriptor usage. Routine scalar accesses allocate no heap
memory. Borrow creation, view creation and worker handoff are setup operations.

See [the shared job sample](../samples/32_shared_jobs.goose) for a complete
worker pool with indexed completion flags and disjoint result ranges.

## Atomic regions and indexed job tables

`shared_atomic_u32(owner, offset, initial)` and `shared_atomic_u64` register
one aligned atomic slot. `shared_atomic_array_u32(owner, offset, count, initial)`
and its u64 counterpart register and initialize a whole typed region, returning
a `SharedView` for that region. Workers obtain an existing slot with
`shared_atomic_view_u32(region, index)` or `shared_atomic_view_u64`. Derivation
checks width, generation and index inline; it allocates no metadata or heap.
This permits one worker argument to carry thousands of completion slots.

Registration rejects read-only storage, out-of-bounds or unaligned ranges,
any overlapping ordinary borrow, and any previously registered atomic bytes.
Atomic ranges remain permanently unavailable to ordinary borrows until close,
even when the atomic capability is no longer used. U32 and u64 regions cannot
partially overlap. Native atomics use host integer representation; endian
scalar conversion does not apply to an atomic range.

`atomic_load(a, order)`, `atomic_store(a, value, order)`,
`atomic_exchange(a, value, order)`, and
`atomic_fetch_add/sub/and/or/xor(a, value, order)` use exactly the handle's
unsigned width. Fetch operations return the old value and arithmetic wraps at
that width. `atomic_compare_exchange(a, expected, desired, success, failure)`
returns `(observed, exchanged)`: on failure, observed is the actual old value.
CAS is strong, with no spurious failures.

Orders are compile-time string literals or named global string constants:
`"Relaxed"`, `"Acquire"`, `"Release"`, `"AcqRel"`, `"SeqCst"`.
Loads reject Release/AcqRel, stores reject Acquire/AcqRel, and CAS failure orders
must be load orders no stronger than success. Every invalid combination is a
compiler error. `atomic_is_lock_free(a)` explicitly reports the supported width.
The current atomic backend requires an always-lock-free native GCC/Clang width;
TinyCC/JIT is rejected before execution because its in-memory backend lacks
TLS support; generated C also gives explicit capability errors for unsupported
frontends, including MSVC. There
is no mutex fallback disguised as lock-free behavior.

Routine atomic operations consist of inline generation/kind/alignment/bounds
checks followed directly by a GCC/Clang atomic builtin with a constant order.
They take no central mutex, call no ordinary application helper and allocate
nothing. The owner thread alone may close, and every worker's allocation lease
prevents close/unmap until worker cleanup. Descriptor generations are published
atomically and stable slabs keep stale handles safe to reject. This lifetime
protocol pins storage through the actual atomic instruction, rather than
merely validating a token before an unprotected access.

## Readonly files, byte buffers and page advice

`shared_map_readonly(path, bytes)` returns `(SharedOwner, bool)`. The size is
explicit, positive and no larger than the file; missing files and OS mapping
failures return false. It uses a readonly file mapping and closes the file and
mapping handles after the view is established. `shared_close` later unmaps the
view. Mapping a file does not snapshot it: external changes can become visible.
The application must keep other actors from truncating a mapped file. External
truncation may cause an OS mapping fault (for example SIGBUS); it is outside
contained Goose abort recovery.

A readonly mapping permits overlapping read borrows across workers. Every
write and atomic registration is refused. `shared_view(view, offset, bytes)`
creates a checked subview, including in workers. A subview preserves readonly
permissions and typed atomic regions; an atomic subview must contain complete,
aligned slots. Views are setup metadata retained until allocation close.

For repeated jobs, use `shared_borrow(view, offset, bytes)` directly. It checks
the requested byte range and creates a reusable access record. Releasing it
reuses that record, so metadata remains bounded by concurrent borrows rather
than job count. The one-argument spelling borrows the entire view.

`memory_read_bytes(access, offset, out)` copies into an existing writable
`u8[:]` buffer; literals, const slices and serialization byte views cannot be
its destination. `memory_write_bytes(access, offset, bytes)` copies from a
read-only byte slice. The buffer length determines the checked byte count.
Neither exposes a Goose reference into shared storage.

`shared_page_advice(view, offset, bytes, advice)` returns `(supported, applied)`.
Advice is a compile-time `"Normal"`, `"Sequential"`, `"Random"`, `"WillNeed"`,
or `"DontNeed"`. POSIX uses the available `madvise` capability; Windows currently
reports unsupported. A supported OS request may fail and reports applied=false.
Advice may cover pages surrounding the byte range. DontNeed is permitted only
for readonly mappings: it is always refused for anonymous live data because
those OS semantics could erase bytes. Advice grants no memory-access rights.

Native type names are reserved at the root for type declarations. A namespaced
user type and a generic parameter can use the same leaf name with normal
lexical priority. `::SharedView` unambiguously names the native type, and type
dumps retain that qualification.
