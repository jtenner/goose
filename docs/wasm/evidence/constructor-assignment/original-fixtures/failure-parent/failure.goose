struct S { a: i64, b: i64 }
var target: S = S { a: 1, b: 2 };
var divisor: i64 = 0;
fn main() { print("before"); target = S { a: 9, b: 8 / divisor }; print("after"); }
