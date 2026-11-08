enum E { A { x: i64 }, B }
fn main() { var a: E = E.A { x: 1 }; var b: E = E.B; print(a == b); }
