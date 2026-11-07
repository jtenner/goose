struct S { n: i64 }
recursive fn work(a: S[2]&, amount: i64) -> i64 {
 var own: S[2] = copy(a); own[0].n += amount;
 var scratch: i64[] = [5];
 defer { assert(scratch[0] == 5); assert(own[1].n == a[1].n); }
 return own[0].n + scratch[0];
}
fn invoke<F>(a: S[2]&) { F(a); }
fn main() {
 var a: S[2] = [S { n: 7 }, S { n: 8 }]; assert(work(a, 1) == 13);
 invoke(a) { p: S[2]& =>
  var own: S[2] = copy(p); own[0].n += 10; var inner: i64[] = [9];
  defer { assert(own[0].n == 17); assert(inner[0] == 9); print("callback"); }
  assert(work(own, 3) == 25); assert(p[0].n == 7);
 };
 var live: i64[] = [91]; assert(work(a, 2) == 14);
 invoke(a) { p: S[2]& =>
  var own: S[2] = copy(p); own[0].n += 10; var inner: i64[] = [9];
  defer { assert(own[0].n == 17); assert(inner[0] == 9); print("callback"); }
  assert(work(own, 3) == 25); assert(p[0].n == 7);
 };
 assert(live[0] == 91); print("callbacks=", a[0].n, ",", a[1].n);
}
