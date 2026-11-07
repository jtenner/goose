struct S { values: i64[2] }
var target: S = S { values: [1,2] };
recursive fn run() -> i64 { target = S { values: [9, { return 7; 8 }] }; return 0; }
fn main() { assert(run() == 7); assert(target.values[0] == 1); assert(target.values[1] == 2); print("array_scalar_exit"); }
