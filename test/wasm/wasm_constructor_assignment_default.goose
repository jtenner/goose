struct Pair { a: i64, b: i64 = observe() }
var target: Pair = Pair { a: 1, b: 2 };
recursive fn observe() -> i64 { target.a }
fn main() { target = Pair { a: 7 }; assert(target.a == 7); assert(target.b == 1); print("default"); }
