extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
fn main() {
    var index: i64 = 0;
    let p = unsafe_capture(&index);
    let a: i64[2] = [11, 22];
    assert(index >= 0 && index < a.len);
    unsafe_store<i64>(p, 2, false);
    print(a[index]); // bce:keep
}
