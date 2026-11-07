struct S { n: i64 }
var calls: i64 = 0;
recursive fn selected(a: S[0]&) -> S[0]& { calls++; return a; }
fn main() {
 var a: S[..3] = [S { n: 1 }, S { n: 2 }]; var total: i64 = 0;
 for s in a { a.clear(); assert(s.n == 1); total += s.n; }
 assert(total == 1); assert(a.len == 0);
 var empty: S[0] = []; for s in selected(empty) { assert(false); }
 var none: S[..3] = []; for s in none { assert(false); }
 var short: S[..3] = [S { n: 1 }]; var longer: S[..3] = [S { n: 10 }, S { n: 20 }, S { n: 30 }];
 var current: S[..3]& = short; total = 0;
 for s in current { current .= longer; total += s.n; }
 assert(total == 51); assert(calls == 1); print("limited=", total, ",", calls);
}
