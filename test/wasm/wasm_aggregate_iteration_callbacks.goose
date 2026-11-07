struct S { n: i64 }
fn invoke<F>(a: S[2]&) { F(a); }
inline fn total(a: S[2]&) -> i64 { var result: i64 = 0; for s in a { result += s.n; } return result; }
fn main() {
 var a: S[2] = [S { n: 1 }, S { n: 2 }];
 invoke(a) { p: S[2]& => var result: i64 = 0; for s in p { result += s.n; } assert(result == 3); assert(total(p) == 3); print("callback=", result); };
}
