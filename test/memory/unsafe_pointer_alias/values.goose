extern fn unsafe_capture(x: i64&) -> UnsafePtr = "unsafe_alias_capture";
extern fn unsafe_pair(x: i64, y: i64) -> i64 = "unsafe_alias_pair";
fn unsafe_write(p: UnsafePtr, value: i64) -> i64 {
    unsafe_store<i64>(p, value, false);
    return 0;
}
fn pair(x: i64, y: i64) -> i64 { x * 10 + y }
var global_value: i64 = 3;
fn main() {
    var value: i64 = 1;
    let alias = &value;
    let p = unsafe_capture(&value);
    let old_plus_zero = value + unsafe_write(p, 7);
    assert(old_plus_zero == 1);
    assert(value == 7 && alias == 7);
    let digits = pair(value, { unsafe_store<i64>(p, 2, false); value });
    assert(digits == 72 && value == 2);
    let foreign_digits = unsafe_pair(value, { unsafe_store<i64>(p, 8, false); value });
    assert(foreign_digits == 28 && alias == 8);
    unsafe_store<i64>(p, value, { unsafe_store<i64>(p, 42, false); false });
    assert(value == 8); // The value argument was copied before the endian argument.
    value += unsafe_write(p, 99);
    assert(value == 8 && alias == 8); // Compound assignment retained its old operand.
    let loaded = unsafe_load<i64>(p, { unsafe_store<i64>(p, 9, false); false });
    assert(loaded == 9 && value == 9);
    let gp = unsafe_capture(&global_value);
    unsafe_store<i64>(gp, 4, false);
    assert(global_value == 4);
    print("unsafe alias values ok");
}
