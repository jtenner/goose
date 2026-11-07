struct S { x: i64 }
var calls: i64 = 0;
recursive fn touch(s: S&) -> S& { calls++; s.x += 1; return s; }
fn invoke<F>(s: S&) { F(s); }
fn main() {
    var s: S = S { x: 7 };
    invoke(s) { p: S& => touch(p); assert(p.x == 8); };
    assert(s.x == 8); assert(calls == 1); print(s.x, ",", calls);
}
