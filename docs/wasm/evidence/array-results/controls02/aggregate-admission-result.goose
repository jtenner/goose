struct S { x: i64 }
recursive fn make(n: i64) -> S[1] { [S { x: n }] }
fn main() { var a: S[1] = make(1); print(a[0].x); }
