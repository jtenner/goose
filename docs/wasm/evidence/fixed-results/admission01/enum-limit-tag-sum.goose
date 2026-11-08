enum Huge { A { bytes: u8[4294967295] }, B }
fn main() { var a: Huge = default<Huge>(); match a { A p => print(p.bytes[0]), B => print(0) } }
