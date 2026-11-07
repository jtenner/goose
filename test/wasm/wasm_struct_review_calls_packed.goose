struct S { x: i64 }
var calls: i64 = 0;
recursive fn touch(s: S&) -> S& { calls++; s.x += 1; return s; }
inline fn inline_touch(s: S&) -> S& {
    calls++; defer { calls += 10; }
    if s.x > 0 { s.x += 2; return s; }
    return s;
}
fn invoke<F>(s: S&) { F(s); }
fn main() {
    var data: i64[] = [99];
    var s: S = S { x: 7 };
    touch(s); assert(s.x == 8); assert(calls == 1);
    inline_touch(s); assert(s.x == 10); assert(calls == 12);
    invoke(s, touch); assert(s.x == 11); assert(calls == 13);
    invoke(s) { p: S& => touch(p); assert(p.x == 12); }; assert(calls == 14);
    var address: S& = touch(s); assert(address .== &s); assert(s.x == 13); assert(calls == 15);
    var copied: S = copy(touch(s)); copied.x += 10;
    assert(s.x == 14); assert(copied.x == 24); assert(calls == 16);
    assert(data[0] == 99);
    print("calls=", s.x, ",", copied.x, ",", calls);
}
