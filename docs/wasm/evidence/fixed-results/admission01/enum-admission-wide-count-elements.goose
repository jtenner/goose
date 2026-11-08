enum E { A { x: i64 }, B }
fn main() { var a: E[u64] = [E.A { x: 1 }]; match a[0] { A p => print(p.x), B => print(0) } }
