enum E { A { x: i64 }, B }
inline fn read(e: E) -> i64 { match e { A p => p.x, B => 0 } }
fn main() { var e: E = E.A { x: 1 }; print(read(e)); }
