struct S { n: i64 }
var target: S = S { n: 1 };
recursive fn run(early: bool) -> i64 {
 defer { if early { assert(target.n == 1); } else { assert(target.n == 9); } print("outer"); }
 target = S { n: { defer { assert(target.n == 1); print("inner"); } if early { return 8; } 9 } };
 return target.n;
}
fn main() { assert(run(true) == 8); assert(run(false) == 9); print("early"); }
