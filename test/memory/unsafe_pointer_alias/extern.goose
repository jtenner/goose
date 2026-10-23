extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
extern fn unsafe_write(p: UnsafePtr, value: i64) = "unsafe_alias_external_store";
fn main() {
    var index: i64 = 0;
    let p = unsafe_capture(&index);
    let a: i64[2] = [11, 22];
    assert(index >= 0 && index < a.len);
    unsafe_write(p, 2);
    print(a[index]); // bce:keep
}
