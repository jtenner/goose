struct Pair { a: i64, b: i64 }
fn main() { var target: Pair = Pair { a: 1, b: 2 }; var alias: Pair& = target; target = Pair { a: 7, b: alias.a }; assert(target.a == 7); assert(target.b == 1); assert(alias .== &target); print("alias"); }
