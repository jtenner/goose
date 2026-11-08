struct S { a:i64, b:i64 }
var target:S = S { a:1, b:2 };
var divisor:i64 = 0;
recursive fn make()->S { return S { a:9, b:8/divisor }; }
fn main() { print("before"); target=make(); print("after"); }
