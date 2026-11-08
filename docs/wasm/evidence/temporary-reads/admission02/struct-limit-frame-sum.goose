struct Huge { a: u8[2147483648] }
fn main() { var x: Huge = default<Huge>(); var y: Huge = default<Huge>(); print(x.a[0], y.a[0]); }
