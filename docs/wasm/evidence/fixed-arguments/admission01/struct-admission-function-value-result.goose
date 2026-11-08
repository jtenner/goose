struct S { x: i64 }
fn apply<F>(n: i64) -> i64 { var s: S = F(n); s.x }
fn main() { print(apply(1) { y => S { x: y } }); }
