struct S { mark: u8, n: u32, tail: u16 }
fn main() {
 var a: S[2] = [S { mark: 11, n: 100, tail: 50001 }, S { mark: 22, n: 200, tail: 60002 }];
 var total: i64 = 0;
 for s, i in a {
  assert(&s .!= &a[i]);
  assert(s.mark == (i + 1) * 11); assert(s.tail == 50001 + i * 10001);
  a[i].n += 1000; assert(s.n == (i + 1) * 100);
  var own: S = copy(s); own.n += 9; assert(own.n == s.n + 9); total += s.n;
 }
 assert(total == 300); assert(a[0].n == 1100); assert(a[1].n == 1200);
 print("values=", total);
}
