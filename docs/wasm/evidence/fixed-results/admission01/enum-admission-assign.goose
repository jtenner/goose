enum E { A { x: i64 }, B }
fn main() { var a: E = E.A { x: 1 }; var b: E = E.B; a = b; match a { A p => print(p.x), B => print(0) } }
