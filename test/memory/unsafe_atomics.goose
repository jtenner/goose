// no-jit
extern fn raw_malloc(n: u64) -> UnsafePtr = "malloc";
extern fn raw_free(p: UnsafePtr) = "free";
thread_fn claim32(address: u64) {
    for i in 10000 { unsafe_atomic_fetch_add<u32>(address, 1, "Relaxed"); }
}
thread_fn claim64(address: u64) {
    for i in 10000 { unsafe_atomic_fetch_add<u64>(address, 1, "Relaxed"); }
}
thread_fn bad(address: u64, width: i64, op: i64) {
    if width == 4 {
        if op == 0 { unsafe_atomic_load<u32>(address, "Relaxed"); }
        if op == 1 { unsafe_atomic_store<u32>(address, 1, "Relaxed"); }
        if op == 2 { unsafe_atomic_fetch_add<u32>(address, 1, "Relaxed"); }
        if op == 3 { unsafe_atomic_compare_exchange<u32>(address, 0, 1, "SeqCst", "Acquire"); }
        if op == 4 { unsafe_atomic_fetch_sub<u32>(address, 1, "Relaxed"); }
        if op == 5 { unsafe_atomic_exchange<u32>(address, 1, "Relaxed"); }
        if op == 6 { unsafe_atomic_fetch_and<u32>(address, 1, "Relaxed"); }
        if op == 7 { unsafe_atomic_fetch_or<u32>(address, 1, "Relaxed"); }
        if op == 8 { unsafe_atomic_fetch_xor<u32>(address, 1, "Relaxed"); }
    } else {
        if op == 0 { unsafe_atomic_load<u64>(address, "Relaxed"); }
        if op == 1 { unsafe_atomic_store<u64>(address, 1, "Relaxed"); }
        if op == 2 { unsafe_atomic_fetch_add<u64>(address, 1, "Relaxed"); }
        if op == 3 { unsafe_atomic_compare_exchange<u64>(address, 0, 1, "SeqCst", "Acquire"); }
        if op == 4 { unsafe_atomic_fetch_sub<u64>(address, 1, "Relaxed"); }
        if op == 5 { unsafe_atomic_exchange<u64>(address, 1, "Relaxed"); }
        if op == 6 { unsafe_atomic_fetch_and<u64>(address, 1, "Relaxed"); }
        if op == 7 { unsafe_atomic_fetch_or<u64>(address, 1, "Relaxed"); }
        if op == 8 { unsafe_atomic_fetch_xor<u64>(address, 1, "Relaxed"); }
    }
}
fn main() {
    let p = raw_malloc(16);
    let address = unsafe_handle_from_ptr(p);
    assert(address != 0);
    assert(unsafe_atomic_is_lock_free<u32>() && unsafe_atomic_is_lock_free<u64>());
    for repeat in 10 {
        unsafe_atomic_store<u32>(address, 0, "Release");
        unsafe_atomic_store<u64>(address + 8, 0, "SeqCst");
        var workers: i64[>..] = [];
        for i in 8 {
            workers.push(thread_spawn(claim32, address));
            workers.push(thread_spawn(claim64, address + 8));
        }
        for id in workers { assert(thread_wait(id)); }
        assert(unsafe_atomic_load<u32>(address, "Acquire") == 80000);
        assert(unsafe_atomic_load<u64>(address + 8, "SeqCst") == 80000);
    }
    let seen32, ok32 = unsafe_atomic_compare_exchange<u32>(address, 80000, 4294967295, "AcqRel", "Acquire");
    assert(ok32 && seen32 == 80000);
    assert(unsafe_atomic_fetch_add<u32>(address, 1, "Release") == 4294967295);
    assert(unsafe_atomic_fetch_sub<u32>(address, 1, "Acquire") == 0);
    assert(unsafe_atomic_load<u32>(address, "Relaxed") == 4294967295);
    assert(unsafe_atomic_exchange<u32>(address, 15, "AcqRel") == 4294967295);
    assert(unsafe_atomic_fetch_and<u32>(address, 7, "SeqCst") == 15);
    assert(unsafe_atomic_fetch_or<u32>(address, 8, "Release") == 7);
    assert(unsafe_atomic_fetch_xor<u32>(address, 3, "Acquire") == 15);
    let old32, failed32 = unsafe_atomic_compare_exchange<u32>(address, 1, 7, "Acquire", "Relaxed");
    assert(!failed32 && old32 == 12);
    let seen64, ok64 = unsafe_atomic_compare_exchange<u64>(address + 8, 80000, 18446744073709551615, "SeqCst", "SeqCst");
    assert(ok64 && seen64 == 80000);
    let old, failed = unsafe_atomic_compare_exchange<u64>(address + 8, 0, 1, "Relaxed", "Relaxed");
    assert(!failed && old == 18446744073709551615);
    assert(unsafe_atomic_fetch_add<u64>(address + 8, 1, "Acquire") == old);
    assert(unsafe_atomic_fetch_sub<u64>(address + 8, 2, "Release") == 0);
    assert(unsafe_atomic_load<u64>(address + 8, "Relaxed") == 18446744073709551614);
    assert(unsafe_atomic_exchange<u64>(address + 8, 15, "AcqRel") == 18446744073709551614);
    assert(unsafe_atomic_fetch_and<u64>(address + 8, 7, "SeqCst") == 15);
    assert(unsafe_atomic_fetch_or<u64>(address + 8, 8, "Release") == 7);
    assert(unsafe_atomic_fetch_xor<u64>(address + 8, 3, "Acquire") == 15);
    for op in 9 {
        assert(!thread_wait(thread_spawn_contained(bad, address + 1, 4, op)));
        assert(!thread_wait(thread_spawn_contained(bad, address + 1, 8, op)));
    }
    raw_free(p);
    print("unsafe atomics ok");
}
