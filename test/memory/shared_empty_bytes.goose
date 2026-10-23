// no-jit
// Default empty slices have null data pointers; zero-byte copies still
// validate access/bounds but must never pass those pointers to memmove.
fn main() {
    let owner, ok = shared_alloc(8); assert(ok);
    let access = shared_borrow(shared_view(owner, 0, 8));
    var empty: u8[:] = default<u8[:]>();
    memory_read_bytes(access, 8, empty);
    memory_write_bytes(access, 8, empty);
    shared_release(access); assert(shared_close(owner));
    print("shared empty byte copies ok");
}
