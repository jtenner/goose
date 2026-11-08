enum E { A { x: i64 }, B }
fn main() { var a: E; a = E.B; match a { A p => print(p.x), B => print(0) } }
