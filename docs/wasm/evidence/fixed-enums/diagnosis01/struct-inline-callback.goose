struct S { x: i64 }
var calls: i64 = 0;
inline fn touch(s: S&) -> S& { calls++; defer { calls += 10; } if calls > 0 { return s; } return s; }
fn invoke<F>(s: S&) { F(s); }
fn main() { var s: S = S { x: 7 }; invoke(s) { p: S& => touch(p); assert(p.x == 7); }; assert(calls == 11); print(calls); }
