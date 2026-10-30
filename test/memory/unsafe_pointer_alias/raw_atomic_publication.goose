extern fn raw_malloc(n: u64) -> UnsafePtr = "malloc";
extern fn raw_free(p: UnsafePtr) = "free";
extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
thread_fn publish(h: u64, start: u64, done: u64) {
    while unsafe_atomic_load<u32>(start, "Acquire") == 0 {}
    unsafe_store<i64>(unsafe_ptr_from_handle(h), 2, false);
    unsafe_atomic_store<u32>(done, 1, "Release");
}
fn main() {
    var index: i64 = 0;
    let handle = unsafe_handle_from_ptr(unsafe_capture(index));
    let values: i64[2] = [11, 22];
    let p = raw_malloc(8);
    let start = unsafe_handle_from_ptr(p);
    assert(start != 0);
    let done = start + 4;
    unsafe_atomic_store<u32>(start, 0, "Relaxed");
    unsafe_atomic_store<u32>(done, 0, "Relaxed");
    let worker = thread_spawn(publish, handle, start, done);
    assert(index >= 0 && index < values.len);
    // The worker cannot write index before this release. Its completion
    // publishes that ordinary scalar write before the later safe access.
    unsafe_atomic_store<u32>(start, 1, "Release");
    while unsafe_atomic_load<u32>(done, "Acquire") == 0 {}
    print(values[index]); // bce:keep
    assert(thread_wait(worker));
    raw_free(p);
}
