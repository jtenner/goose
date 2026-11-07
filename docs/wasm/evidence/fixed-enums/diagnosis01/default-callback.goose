fn init<F>() -> i64 { var x: i64 = 0; F(x); return x; }
struct S { x: i64 = init() { n: i64& => var delta: i64 = 3; n += delta; } }
fn main() { var s: S = default<S>(); assert(s.x == 3); print(s.x); }
