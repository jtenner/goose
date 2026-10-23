extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
thread_fn publish(h: u64, start: SharedAtomicU32, done: SharedAtomicU32) {
    while atomic_load(start, "Acquire") == 0 {}
    unsafe_store<i64>(unsafe_ptr_from_handle(h), 2, false);
    atomic_store(done, 1, "Release");
}
fn main() {
    var index: i64 = 0;
    let handle = unsafe_handle_from_ptr(unsafe_capture(index));
    let values: i64[2] = [11, 22];
    let owner, ok = shared_alloc(16);
    assert(ok);
    let start = shared_atomic_u32(owner, 0, 0);
    let done = shared_atomic_u32(owner, 4, 0);
    let worker = thread_spawn(publish, handle, start, done);
    assert(index >= 0 && index < values.len);
    // The worker cannot write index before this release. Its completion
    // publishes that ordinary scalar write before the later safe access.
    atomic_store(start, 1, "Release");
    while atomic_load(done, "Acquire") == 0 {}
    print(values[index]); // bce:keep
    assert(thread_wait(worker));
    assert(shared_close(owner));
}
