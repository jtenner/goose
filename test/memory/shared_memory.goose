// no-jit
// Native capabilities, demand-zero storage, checked unaligned endian scalars,
// exclusive ranges, copies, stale aliases and explicit close results.
thread_fn misuse(v: SharedView, kind: i64) {
    if kind == 0 { shared_borrow(v); }
    let a = shared_borrow(v);
    if kind == 1 { memory_read<u64>(a, 57, false); }
    if kind == 2 { memory_write<u32>(a, 18446744073709551615, 1, false); }
    if kind == 3 { shared_release(a); memory_read<u8>(a, 0, false); }
    if kind == 4 { shared_borrow(v); }
}
fn main() {
    let invalid, failed = shared_alloc(18446744073709551615);
    assert(!failed);
    assert(!shared_close(invalid));
    let owner, ok = shared_alloc(64);
    assert(ok && shared_size(owner) == 64);
    let v = shared_view(owner, 0, 64);
    let a = shared_borrow(v);
    assert(memory_read<u64>(a, 1, false) == 0);
    memory_write<i8>(a, 0, -7, false);
    memory_write<u16>(a, 1, 4660, false);
    memory_write<i32>(a, 3, -1234567, true);
    memory_write<u64>(a, 7, 18446744073709551615, true);
    assert(memory_read<i8>(a, 0, true) == -7);
    assert(memory_read<u8>(a, 1, false) == 52);
    assert(memory_read<u16>(a, 1, true) == 13330);
    assert(memory_read<i32>(a, 3, true) == -1234567);
    assert(memory_read<u64>(a, 7, true) == 18446744073709551615);
    memory_copy(a, 24, a, 1, 14);
    assert(memory_read<u16>(a, 24, false) == 4660);
    assert(!shared_close(owner));
    shared_release(a);
    for kind in 1..5 { assert(!thread_wait(thread_spawn_contained(misuse, v, kind))); }
    let b = shared_borrow(v); // Each abort removed its abandoned borrow.
    shared_release(b);
    assert(shared_close(owner));
    assert(!shared_close(owner));
    assert(!thread_wait(thread_spawn_contained(misuse, v, 0)));
    let next, next_ok = shared_alloc(64);
    assert(next_ok);
    assert(!thread_wait(thread_spawn_contained(misuse, v, 0))); // Slot reuse must not revive v.
    assert(shared_close(next));
    print("shared memory ok");
}
