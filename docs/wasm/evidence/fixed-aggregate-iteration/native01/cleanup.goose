struct Big { bytes: u8[40000], n: i64 }
recursive fn check(a: Big[2]&, early: bool) -> i64 {
 var total: i64 = 0;
 defer { for e in a { assert(e.bytes[39999] == 7); } }
 for e in a {
  var scratch: i64[] = [9];
  defer { assert(scratch[0] == 9); assert(e.bytes[39999] == 7); print("defer=", e.n); }
  if early { return e.n; } total += e.n;
 }
 return total;
}
fn main() {
 var a: Big[2] = [Big { bytes: [7; 40000], n: 3 }, Big { bytes: [7; 40000], n: 4 }];
 assert(check(a, true) == 3); var live: i64[] = [91]; assert(check(a, false) == 7); assert(live[0] == 91);
 for e, i in a { var scratch: i64[] = [5]; defer { assert(scratch[0] == 5); print("loop=", e.n); } if i == 0 { continue; } break; }
 print("cleanup");
}
