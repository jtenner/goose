struct Huge { a: u8[2147483648], b: u8[2147483648] }
fn main() { var h: Huge = default<Huge>(); print(h.a[0], h.b[0]); }
