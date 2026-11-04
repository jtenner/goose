// Copy-out must use the same data-stack storage as an ordinary large return.
fn main() {
    let pointer, owner, ok = shared_pointer_alloc<u8[9000000]>([7; 9000000]);
    assert(ok);
    let value = shared_pointer_copy(pointer);
    assert(value[0] == 7 && value[8999999] == 7);
    shared_pointer_store(pointer, [9; 9000000]);
    let second = shared_pointer_copy(pointer);
    assert(value[0] == 7 && second[8999999] == 9);
    shared_pointer_release(pointer);
    assert(shared_close(owner));
    print(second[8999999]);
}
