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

Capability records occupy stable reusable metadata slabs. Mapping storage is
released on close; the slabs retain generation tombstones and grow only with
peak simultaneous descriptor usage. Routine scalar accesses allocate no heap
memory. Borrow creation, view creation and worker handoff are setup operations.

## Explicitly unsafe C pointer interoperability

`UnsafePtr` is an opaque raw object pointer, separate from every safe shared
capability. These operations are **not memory-safe**. Their names mark the
unsafe boundary; Goose does not add an `unsafe` block or infer pointer access
from an integer.

The root type name `UnsafePtr` is reserved, like the safe native type names.
Namespaced user types and bound generic parameters keep their normal lexical
priority; `::UnsafePtr` explicitly names the root native type.

| Intrinsic | Result |
| --- | --- |
| `unsafe_ptr_from_handle(handle: u64)` | `UnsafePtr`, after an address-width check; zero is null |
| `unsafe_handle_from_ptr(pointer: UnsafePtr)` | `u64`, zero for null |
| `unsafe_ptr_add(pointer: UnsafePtr, byte_offset: i64)` | `UnsafePtr`, after checked signed address arithmetic |
| `unsafe_load<T>(pointer: UnsafePtr, big_endian: bool)` | `T` |
| `unsafe_store<T>(pointer: UnsafePtr, value: T, big_endian: bool)` | No result |

`T` is exactly `i8/i16/i32/i64/u8/u16/u32/u64`. `false` means little endian;
`true` means big endian, independently of the host. Loads and stores copy the
scalar bytes with `memcpy` and assemble/disassemble their bits. Packed,
unaligned scalar storage is supported; no typed, potentially unaligned C
lvalue is dereferenced. These operations are ordinary non-atomic copies and
are unsuitable for volatile device memory or concurrent atomic storage.

The caller must guarantee all of the following for each raw access:

- The pointer has valid provenance from a live C allocation or object, and
  the complete scalar byte range belongs to that object. An integer address
  alone does not establish provenance or make storage valid.
- The object remains alive throughout the access; stores have permission to
  write every byte. Retaining a pointer or a handle does not retain its object.
- Object representation, aliasing/effective-type rules and synchronization
  permit the byte access. Unaligned copies remove the scalar alignment
  requirement only; they do not remove the object's own alignment or C ABI
  requirements, data races, borrow conflicts, or lifetime obligations.
- Pointer arithmetic remains within the same live object (or one past it,
  without dereferencing there). A numerical overflow check cannot prove this.
  The computed integer address must convert back to the intended object
  pointer on the target C implementation. No provenance is fabricated by
  arithmetic or by a handle conversion.

Null loads, stores and additions abort, including adding zero to null.
Loads/stores check numerical overflow of the complete scalar address range;
addition checks underflow and overflow even for `i64.min`. Checks apply in
release and debug builds. They cannot detect dangling pointers, unmapped
addresses, object bounds violations, readonly memory, alias violations, or
races. Violating the caller obligations can crash or cause undefined behavior.
Converting null to/from handle zero is allowed. There is no implicit default
constructor for `UnsafePtr`; use the explicit conversion to create null.

The native ABI is C `void *`. A direct extern may accept or return `UnsafePtr`
for an object-pointer parameter or result; the whole extern call is an unsafe
C boundary. For example, tests declare libc `malloc`/`free` directly. Match
all parameters, results, calling conventions, alignment and ownership rules
against the real C signature. Function pointers and capability pointers are
not supported. Existing externs returning opaque `u64` object addresses may
be adapted explicitly with `unsafe_ptr_from_handle`; merely calling a
returned integer a handle provides no validity guarantee.

The current C backend lays out pointers in eight bytes. Generated code checks
`UINTPTR_MAX == UINT64_MAX` and the sizes of `void *` and `uintptr_t`, and
rejects other targets explicitly instead of narrowing addresses or silently
changing packed layouts. This requires the target's conventional flat-address
object-pointer/integer roundtrip ABI. Address conversion never truncates.

Safe owners, views, accesses and atomic capabilities cannot convert to or from
raw pointers, handles, integer casts, byte images or extern signatures. The
unsafe intrinsics do not expose shared mappings or bypass their registry.
`UnsafePtr` also cannot use numeric casts, serialization, queues, worker
arguments (including nested values), or worker globals. A programmer who
explicitly sends a numeric handle and reconstructs a pointer inside a worker
has created another unsafe boundary and must arrange lifetime, ownership,
permissions and synchronization themselves. There is no implicit handoff or
lease for raw C objects, and no general garbage collector.

The scalar copies and address arithmetic are emitted as compiler intrinsics,
with no heap allocations, registry calls or application helpers on the hot
path. Run `python3 test/unsafe_pointer.py --exe build/goose` for the dedicated
GCC/Clang, debug/release and ASan/UBSan matrix (alignment checking enabled).

A valid raw store may target an ordinary writable Goose scalar whose address
was exposed to C. The compiler treats `unsafe_store` as an unknown write for
bounds analysis, including through non-inlined wrappers. It invalidates facts
about reachable storage instead of retaining bounds established before the
write. C extern calls have the same conservative effect: a call can use a raw
pointer or a reference retained by an earlier call even when its current
signature has no reference argument. Previously evaluated operands keep their
snapshotted values; later reads observe the write. The alias regressions in
`test/unsafe_pointer_alias.py` exercise these cases as part of the matrix.

The pre-existing `stdlib/ffi.goose` `cstr` and `bytes` helpers still accept
opaque `u64` addresses and trust C pointer/length validity. They copy results
but cannot validate provenance, termination, lifetime or accessible bounds;
their older names do not make those raw operations memory-safe. The explicit
pointer API does not change or weaken safe shared-memory operations.
