struct S { n: i64 }
struct Outer { first: S, last: S }
var target: Outer = Outer { first: S { n: 1 }, last: S { n: 2 } };
recursive fn run() -> i64 { target = Outer { first: S { n: 9 }, last: { assert(target.first.n == 1); return 7; S { n: 8 } } }; return 0; }
fn main() { assert(run() == 7); assert(target.first.n == 1); assert(target.last.n == 2); print("aggregate_exit"); }
