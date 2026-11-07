struct S { a: i64, b: i64 }
var target: S = S { a: 1, b: 2 };
recursive fn run() -> i64 { target = S { a: 9, b: { assert(target.a == 1); return 7; 8 } }; return 0; }
fn main() { assert(run() == 7); assert(target.a == 1); assert(target.b == 2); print("abandon"); }
