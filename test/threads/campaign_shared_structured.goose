// Composition of structured joins, channel leases, capability atomics and
// SharedPointer claims. A later spawn argument must not take outer leases.
thread_fn inner() -> i64 { 1 }
fn nested_argument() -> i64 {
    let value, ok = thread_join(thread_spawn_join(inner));
    assert(ok);
    value
}
thread_fn publish(p: SharedPointer<i64>, ch: Channel<i64>, cell: SharedAtomicU64,
                  extra: i64) -> i64 {
    let value = shared_pointer_copy(p);
    assert(channel_send(ch, value));
    assert(atomic_fetch_xor(cell, 3, "Release") == 5);
    value + extra
}
thread_fn cancelled(p: SharedPointer<i64>, ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    assert(!ok && thread_cancelled());
    shared_pointer_copy(p)
}
fn main() {
    let owner, ok = shared_alloc(16);
    assert(ok);
    let cell = shared_atomic_u64(owner, 0, 5);
    let pointer, pok = shared_pointer_alloc<i64>(owner, 8, 7);
    assert(pok);
    let ch = channel<i64>(1);
    let worker = thread_spawn_contained_join(publish, pointer, ch, cell, nested_argument());
    let result, joined = thread_join(worker);
    let message, received = channel_receive(ch);
    assert(joined && received && result == 8 && message == 7);
    assert(atomic_load(cell, "Acquire") == 6);
    assert(shared_pointer_copy(pointer) == 7);
    let blocked = thread_spawn_contained_join(cancelled, shared_pointer_retain(pointer), ch);
    assert(thread_cancel(blocked));
    let final, done = thread_join(blocked);
    assert(done && final == 7);
    shared_pointer_release(pointer);
    assert(shared_close(owner));
    print(result, " ", message, " ", final);
}
