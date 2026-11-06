fn wrap(x: f64) -> i64 { return x as! i64; }
fn unsigned(x: f64) -> u64 { return x as! u64; }
fn narrow(x: f64) -> i8 { return x as! i8; }
fn float32(x: f32) -> i64 { return x as! i64; }
fn main() {
    var value = -9223372036854775808.0;
    print(wrap(value));
    value = -9223372036854777856.0;
    print(wrap(value));
    value = 9223372036854774784.0;
    print(wrap(value));
    value = 9223372036854775808.0;
    print(wrap(value), ",", unsigned(value));
    value = 18446744073709549568.0;
    print(wrap(value), ",", unsigned(value));
    value = 18446744073709551616.0;
    print(wrap(value), ",", unsigned(value));
    value = 1.0e100;
    print(wrap(value));
    value = -1.0e100;
    print(wrap(value));
    value = -0.0;
    print(wrap(value));
    value = -3.75;
    print(wrap(value), ",", unsigned(value));
    value = 300.5;
    print(narrow(value));
    var zero = 0.0;
    print(wrap(zero / zero));
    var single: f32 = -1.5;
    print(float32(single));
}
