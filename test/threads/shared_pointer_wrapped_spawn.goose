fn retained(pointer: SharedPointer<i64>) -> SharedPointer<i64> {
    shared_pointer_retain(pointer)
}
thread_fn use_pointer(pointer: SharedPointer<i64>) {
    assert(shared_pointer_copy(pointer) == 7);
}
fn main() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok && thread_wait(thread_spawn(use_pointer, retained(pointer))));
    shared_pointer_release(pointer);
    assert(shared_close(owner));
}
