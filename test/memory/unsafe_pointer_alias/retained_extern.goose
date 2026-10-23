extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
extern fn unsafe_write_saved(value: i64) = "unsafe_alias_saved_store";
fn main() {
    var index: i64 = 0;
    unsafe_capture(index);
    let a: i64[2] = [11, 22];
    assert(index >= 0 && index < a.len);
    unsafe_write_saved(2);
    print(a[index]); // bce:keep
}
