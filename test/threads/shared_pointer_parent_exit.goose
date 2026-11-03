thread_fn child(pointer: SharedPointer<i64>) {
    qget<u8>();
    print(shared_pointer_copy(pointer));
}
thread_fn parent(pointer: SharedPointer<i64>) {
    assert(qput(thread_spawn(child, pointer)));
}
fn main() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok && thread_wait(thread_spawn(parent, pointer)));
    let child_id = qget<i64>();
    let signal: u8 = 1;
    assert(qput(signal) && thread_wait(child_id));
    shared_pointer_release(pointer);
    assert(shared_close(owner));
}
