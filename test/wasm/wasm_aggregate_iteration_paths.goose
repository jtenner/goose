struct S { n: i64 }
var calls: i64 = 0;
recursive fn index() -> i64 { calls++; return 0; }
fn main() {
 var a: S[3] = [S { n: 1 }, S { n: 2 }, S { n: 3 }]; var b: S[3] = [S { n: 10 }, S { n: 20 }, S { n: 30 }];
 var refs: S[3]&[1] = [a]; var total: i64 = 0;
 for s, i in refs[index()] { refs[0] .= b; assert(s.n == (if i == 0 { 1 } else { (i + 1) * 10 })); total += s.n; }
 assert(calls == 1); assert(total == 51);
 var current: S[3]& = a; total = 0;
 for s in current { current .= b; total += s.n; }
 assert(total == 51);
 let alias .= current; total = 0;
 for s in alias { current .= a; total += s.n; }
 assert(total == 60); print("paths=", calls, ",", total);
}
