struct S { n: i64 }
fn main() {
 var outer: i64[] = [91]; var a: S[2] = [S { n: 1 }, S { n: 2 }];
 for s, i in a {
  { var inner: i64[] = [7]; assert(inner[0] == 7); print("inner"); }
  assert(outer[0] == 91); print("restored");
  if i == 0 { var scratch: i64[] = [8]; defer { assert(scratch[0] == 8); print("continue"); } continue; }
  assert(s.n == 2);
 }
 print("after");
}
