struct Empty {}
fn main() {
 var a: Empty[2] = [Empty {}, Empty {}]; var visits: i64 = 0;
 for e, i in a {
  assert(&e .!= &a[i]); let outer .= e;
  for f, j in a { assert(&f .!= outer); assert(&f .!= &a[j]); visits++; }
 }
 assert(visits == 4); print("identity=", visits);
}
