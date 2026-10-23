extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
thread_fn unsafe_worker(h: u64) {
    unsafe_store<i64>(unsafe_ptr_from_handle(h), 2, false);
}
fn main() {
    var index: i64 = 0;
    let h = unsafe_handle_from_ptr(unsafe_capture(index));
    let a: i64[2] = [11, 22];
    assert(index >= 0 && index < a.len);
    assert(thread_wait(thread_spawn(unsafe_worker, h)));
    print(a[index]); // bce:keep
}
