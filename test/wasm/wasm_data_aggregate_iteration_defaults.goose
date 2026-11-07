struct S { n: i64 }
inline fn sum() -> i64 { var a: S[] = [S { n: 1 }, S { n: 2 }]; var total: i64 = 0; for s in a { total += s.n; } return total; }
struct Box { n: i64 = sum() }
var global: Box = default<Box>();
var scalar: i64 = sum();
fn main() { var b: Box = default<Box>(); assert(global.n == 3); assert(scalar == 3); assert(b.n == 3); print("default=", b.n); }
