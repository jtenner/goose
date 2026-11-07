enum E { Data { n: i64 }, Other { b: u8[3] }, Empty }
fn main() {
 var a: E[3] = [E.Data { n: 7 }, E.Other { b: [1, 2, 3] }, E.Empty];
 var total: i64 = 0;
 for e, i in a {
  assert(&e .!= &a[i]);
  match e { Data p => { var own: E.Data = copy(p); own.n += 10; assert(p.n == 7); total += p.n; }, Other p => { assert(p.b[2] == 3); total += p.b[2]; }, Empty => total += 1 }
 }
 var variants: E.Data[2] = [E.Data { n: 10 }, E.Data { n: 20 }];
 for p in variants { total += p.n; }
 assert(total == 41); print("enums=", total);
}
