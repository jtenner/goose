struct Cell { n: i64 }
struct S { values: Cell[..2] }
var target: S = S { values: [Cell { n: 1 },Cell { n: 2 }] };
recursive fn run() -> i64 { target = S { values: [Cell { n: 9 }, { return 7; Cell { n: 8 } }] }; return 0; }
fn main() { assert(run() == 7); assert(target.values[0].n == 1); assert(target.values[1].n == 2); print("array_aggregate_limited_exit"); }
