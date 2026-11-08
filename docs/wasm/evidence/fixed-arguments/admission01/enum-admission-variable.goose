enum V { A { bytes: u8[] }, B }
fn main() { var a: V.. = V.A { bytes: [1] }; match a { A p => print(p.bytes[0]), B => print(0) } }
