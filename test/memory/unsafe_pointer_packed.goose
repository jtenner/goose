// no-jit runtime-debug: internal packed pointer storage must support alignment 1.
extern fn unsafe_packed_malloc(n: u64) -> UnsafePtr = "malloc";
extern fn unsafe_packed_free(p: UnsafePtr) = "free";
struct UnsafePointerHolder { prefix: u8, pointer: UnsafePtr }
fn pointer_identity(p: UnsafePtr) -> UnsafePtr { p }
fn holder_identity(h: UnsafePointerHolder) -> UnsafePointerHolder { h }
fn field_read(p: UnsafePtr&) -> UnsafePtr { p }
fn field_write(p: UnsafePtr&, value: UnsafePtr) { p = value; }
fn array_read(p: UnsafePtr[:], index: i64) -> UnsafePtr { p[index] }
fn main() {
    let p = unsafe_packed_malloc(16);
    assert(unsafe_handle_from_ptr(p) != 0);
    unsafe_store<u64>(p, 42, false);
    let shifted = unsafe_ptr_add(p, 1);
    // The default variable-array length header is four bytes.
    var pointers: UnsafePtr[] = [p, pointer_identity(p)];
    var holders: UnsafePointerHolder[] = [
        UnsafePointerHolder { prefix: 1, pointer: p },
        UnsafePointerHolder { prefix: 2, pointer: p }
    ];
    assert(unsafe_load<u64>(pointers[1], false) == 42);
    let copied_pointers = pointers;
    assert(unsafe_load<u64>(array_read(copied_pointers, 0), false) == 42);
    let copied_holders = holders;
    let copied_holder = holder_identity(copied_holders[1]);
    assert(copied_holder.prefix == 2);
    assert(unsafe_load<u64>(copied_holder.pointer, false) == 42);
    field_write(holders[0].pointer, shifted);
    assert(unsafe_handle_from_ptr(field_read(holders[0].pointer)) == unsafe_handle_from_ptr(p) + 1);
    holders[1].pointer = pointer_identity(field_read(holders[0].pointer));
    assert(unsafe_handle_from_ptr(holders[1].pointer) == unsafe_handle_from_ptr(p) + 1);
    field_write(pointers[0], shifted);
    assert(unsafe_handle_from_ptr(array_read(pointers, 0)) == unsafe_handle_from_ptr(p) + 1);
    var growable: UnsafePtr[>..] = [];
    growable.push(p);
    growable.push(pointer_identity(shifted));
    assert(unsafe_handle_from_ptr(growable[1]) == unsafe_handle_from_ptr(p) + 1);
    unsafe_packed_free(p);
    print("packed pointers ok");
}
