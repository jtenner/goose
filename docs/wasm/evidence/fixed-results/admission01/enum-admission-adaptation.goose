enum E { A { x: i64 }, B }
fn main() { var a: E.A = E.A { x: 1 }; var b: E = a; match b { A p => print(p.x), B => print(0) } }
