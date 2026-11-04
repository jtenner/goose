fn alias(p: SharedPointer<i64>) -> SharedPointer<i64> { p }

thread_fn transferred_child(p: SharedPointer<i64>) {
    let go = qget<u8>();
    print(shared_pointer_copy(p));
}

thread_fn transferring_parent(p: SharedPointer<i64>) {
    let child = thread_spawn(transferred_child, alias(p));
    assert(qput(child));
}

fn main() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok && thread_wait(thread_spawn(transferring_parent, pointer)));
    let child = qget<i64>();
    let go: u8 = 1;
    assert(qput(go) && thread_wait(child));
    shared_pointer_release(pointer);
    assert(shared_close(owner));
}
