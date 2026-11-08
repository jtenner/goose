struct S { x: i64 }
recursive fn make(n: i64) -> S { S { x: n } }
fn main() { var s: S = make(1); print(s.x); }
