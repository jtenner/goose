extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
thread_fn unsafe_worker(h: u64) {
    let start = qget<i64>();
    assert(start == 1);
    unsafe_store<i64>(unsafe_ptr_from_handle(h), 2, false);
    qput(1 as u64);
}
fn main() {
    var index: i64 = 0;
    let h = unsafe_handle_from_ptr(unsafe_capture(index));
    let a: i64[2] = [11, 22];
    let worker = thread_spawn(unsafe_worker, h);
    assert(index >= 0 && index < a.len);
    qput(1); // The worker cannot write the index before this signal.
    let done = qget<u64>(); // Completion publishes the scalar write.
    assert(done == 1);
    print(a[index]); // bce:keep
    assert(thread_wait(worker));
}
