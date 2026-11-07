enum E { V { n: i64 }, Stop }
var a: E = E.V { n: 11 }; var b: E = E.V { n: 22 }; var current: E& = a; var calls: i64 = 0;
recursive fn get() -> E& { calls++; return current; }
inline fn touch(e: E&) -> E& { calls++; defer { calls += 10; } if calls > 0 { return e; } return e; }
fn invoke<F>(e: E&) { F(e); }
fn main() {
 match get() { V p => { current .= b; assert(p.n == 11); var q: E.V = copy(p); q.n = 99; assert(p.n == 11); }, Stop => assert(false) }
 assert(calls == 1); assert(current .== b); var copied: E = copy(get()); assert(calls == 2);
 match copied { V p => assert(p.n == 22), Stop => assert(false) }
 touch(a); assert(calls == 13); var copyOfA: E = copy(touch(a)); assert(calls == 24);
 invoke(a) { p: E& => touch(p); assert(calls == 35); };
 match copyOfA { V p => assert(p.n == 11), Stop => assert(false) }
 print("capture=", calls);
}
