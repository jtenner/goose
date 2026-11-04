thread_fn inner() {}
fn start_inner() -> i64 {
    assert(thread_wait(thread_spawn(inner)));
    return 0;
}
thread_fn outer(p: SharedPointer<i64>, unused: i64) {
    print(shared_pointer_copy(p));
}
thread_fn outer_view(view: SharedView, unused: i64) {
    let go = qget<u8>();
    let access = shared_borrow(view);
    assert(memory_read<u32>(access, 0, false) == 0);
    shared_release(access);
}
fn main() {
    let p, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok);
    assert(thread_wait(thread_spawn(outer, p, start_inner())));
    assert(thread_wait(thread_spawn(outer, shared_pointer_retain(p), start_inner())));
    shared_pointer_release(p);
    assert(shared_close(owner));

    let vo, vok = shared_alloc(8);
    assert(vok);
    let view = shared_view(vo, 0, 8);
    let child = thread_spawn(outer_view, view, start_inner());
    assert(!shared_close(vo));
    let go: u8 = 1;
    assert(qput(go) && thread_wait(child));
    assert(shared_close(vo));
}
