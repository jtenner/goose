enum E { A { x: i64 }, B }
fn main() { var a: E = E.A { x: 1 }; var n: i64 = match a { A p => p.x, B => 0 }; print(n); }
