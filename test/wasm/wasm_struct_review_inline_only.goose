struct S { x: i64 }
var calls: i64 = 0;
inline fn touch(s: S&) -> S& {
    calls++; defer { calls += 10; }
    if s.x > 0 { s.x += 1; return s; }
    return s;
}
fn main() { var s: S = S { x: 7 }; touch(s); assert(s.x == 8); assert(calls == 11); print(s.x, ",", calls); }
