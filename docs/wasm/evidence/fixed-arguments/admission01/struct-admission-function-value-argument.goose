struct S { x: i64 }
fn apply<F>(x: S&) -> i64 { F(copy(x)) }
fn main() { var s: S = S { x: 1 }; print(apply(s) { y => y.x }); }
