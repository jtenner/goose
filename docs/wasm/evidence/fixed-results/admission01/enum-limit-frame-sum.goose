enum Huge { A { bytes: u8[2147483648] }, B }
fn main() { var a: Huge = default<Huge>(); var b: Huge = default<Huge>(); match a { A p => print(p.bytes[0]), B => print(0) }; match b { A p => print(p.bytes[0]), B => print(0) } }
