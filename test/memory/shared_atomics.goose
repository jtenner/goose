// no-jit
thread_fn claim(next: SharedAtomicU32, total: SharedAtomicU64, flags: SharedView) {
    loop {
        let job = atomic_fetch_add(next, 1, "Relaxed");
        if job >= 4000 { break; }
        let flag = shared_atomic_view_u32(flags, job);
        atomic_fetch_add(total, (job + 1) as u64, "Relaxed");
        atomic_store(flag, 1, "Release");
    }
}
thread_fn publication(flag: SharedAtomicU32, data: SharedView) {
    let a = shared_borrow(data);
    memory_write<u64>(a, 1, 123456789, false);
    shared_release(a);
    atomic_store(flag, 1, "Release");
}
thread_fn atomic_bad(kind: i64) {
    let o, ok = shared_alloc(64); assert(ok);
    if kind == 0 { shared_atomic_u32(o, 1, 0); }
    if kind == 1 { shared_atomic_u64(o, 60, 0); }
    let a = shared_atomic_u64(o, 0, 0);
    if kind == 2 { shared_atomic_u32(o, 4, 0); }
    if kind == 3 { shared_borrow(shared_view(o, 0, 1)); }
    if kind == 4 { assert(shared_close(o)); atomic_load(a, "Relaxed"); }
    if kind == 5 {
        let flags = shared_atomic_array_u32(o, 16, 2, 0);
        shared_atomic_view_u32(flags, 2);
    }
}
fn main() {
    let o, ok = shared_alloc(16128); assert(ok);
    let n = shared_atomic_u32(o, 0, 0);
    let total = shared_atomic_u64(o, 8, 0);
    let flags = shared_atomic_array_u32(o, 128, 4000, 0);
    assert(atomic_is_lock_free(n) && atomic_is_lock_free(total));
    var workers: i64[>..] = [];
    for i in 8 { workers.push(thread_spawn(claim, n, total, flags)); }
    for id in workers { assert(thread_wait(id)); }
    assert(atomic_load(total, "Acquire") == 8002000);
    for job in 4000 { assert(atomic_load(shared_atomic_view_u32(flags, job), "Acquire") == 1); }
    atomic_store(n, 4294967295, "Relaxed");
    assert(atomic_fetch_add(n, 1, "AcqRel") == 4294967295);
    assert(atomic_fetch_sub(n, 1, "Release") == 0);
    assert(atomic_exchange(n, 15, "Acquire") == 4294967295);
    assert(atomic_fetch_and(n, 7, "SeqCst") == 15);
    assert(atomic_fetch_or(n, 8, "Relaxed") == 7);
    assert(atomic_fetch_xor(n, 3, "Relaxed") == 15);
    let seen, swapped = atomic_compare_exchange(n, 12, 99, "AcqRel", "Acquire");
    assert(swapped && seen == 12);
    let old, failed = atomic_compare_exchange(n, 12, 7, "SeqCst", "Relaxed");
    assert(!failed && old == 99);
    atomic_store(total, 18446744073709551615, "SeqCst");
    assert(atomic_fetch_add(total, 1, "Relaxed") == 18446744073709551615);
    assert(atomic_load(total, "Relaxed") == 0);
    assert(shared_close(o));
    let p, yes = shared_alloc(64); assert(yes);
    let ready = shared_atomic_u32(p, 0, 0);
    let bytes = shared_view(p, 16, 16);
    let worker = thread_spawn(publication, ready, bytes);
    while atomic_load(ready, "Acquire") == 0 {}
    let a = shared_borrow(bytes);
    assert(memory_read<u64>(a, 1, false) == 123456789);
    shared_release(a);
    assert(thread_wait(worker)); assert(shared_close(p));
    for kind in 6 { assert(!thread_wait(thread_spawn_contained(atomic_bad, kind))); }
    print("shared atomics ok");
}
