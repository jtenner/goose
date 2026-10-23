extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
extern fn unsafe_write_handle(p: u64, value: i64) = "unsafe_alias_handle_store";
fn main() {
    var index: i64 = 0;
    let h = unsafe_handle_from_ptr(unsafe_capture(index));
    let a: i64[2] = [11, 22];
    assert(index >= 0 && index < a.len);
    unsafe_write_handle(h, 2);
    print(a[index]); // bce:keep
}
