fn alias(p: SharedPointer<i64>) -> SharedPointer<i64> { p }

thread_fn sink(a: SharedPointer<i64>, b: SharedPointer<i64>) {
    assert(shared_pointer_copy(a) == shared_pointer_copy(b));
}

thread_fn duplicate(p: SharedPointer<i64>) {
    thread_spawn(sink, alias(p), alias(p));
}

fn main() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok);
    print(thread_wait(thread_spawn_contained(duplicate, pointer)));
    shared_pointer_release(pointer);
    assert(shared_close(owner));
}
