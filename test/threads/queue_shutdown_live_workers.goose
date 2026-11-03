thread_fn blocked_plain() { qget<i64>(); }
thread_fn poll_plain() { while true { qpoll<u8>(); } }
thread_fn produce_plain() { while qput(true) {} }
thread_fn blocked_pointer() { qget<SharedPointer<i64>>(); }
thread_fn produce_pointer() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok);
    qput(pointer);
}
fn main() {
    thread_spawn(blocked_plain);
    thread_spawn(poll_plain);
    thread_spawn(produce_plain);
    thread_spawn(blocked_pointer);
    thread_spawn(produce_pointer);
}
