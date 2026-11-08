enum E { A { x: i64 }, B }
recursive fn make(n: i64) -> E { E.A { x: n } }
fn main() { var e: E = make(1); match e { A p => print(p.x), B => print(0) } }
