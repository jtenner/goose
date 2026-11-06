fn identity(x: i64&) -> i64& { return x; }
fn narrow(x: i8&) -> i8& { return x; }
fn fractional(x: f32&) -> f32& { return x; }
fn boolean(x: bool&) -> bool& { return x; }
fn main() {
    var value = 7;
    let copied = identity(value);
    value += 1;
    print(copied, ",", identity(value));
    var byte: i8 = -128;
    let wide: i64 = narrow(byte);
    print(wide);
    var f: f32 = 0.1;
    let double: f64 = fractional(f);
    print(double);
    var b = true;
    print(boolean(b));
}
