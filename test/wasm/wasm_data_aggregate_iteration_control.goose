struct S { mark: u8, n: u32, tail: u16 }
fn main() {
 var a: S[] = [S { mark: 11, n: 100, tail: 50001 }, S { mark: 22, n: 200, tail: 60002 }];
 for s, i in a {
  assert(s.mark == (i + 1) * 11);
  assert(s.tail == 50001 + i * 10001);
  a[i].n += 1000;
  assert(s.n == (i + 1) * 100);
  print("iteration");
 }
}
