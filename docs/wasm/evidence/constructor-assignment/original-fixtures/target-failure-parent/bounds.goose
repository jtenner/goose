struct S { n: i64 }
var index: i64 = 1;
recursive fn effect() -> i64 { print("rhs"); return 9; }
fn main() { var rows: S[] = [S { n:1 }]; print("before"); rows[index] = S { n:effect() }; print("after"); }
