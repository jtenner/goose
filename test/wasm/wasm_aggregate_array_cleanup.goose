struct Big { bytes: u8[40000], n: i64 }
recursive fn check(a: Big[2]&, early: bool) -> i64 {
 var total: i64 = 0;
 for &e in a {
  var saved: Big = copy(e); defer { var scratch: i64[] = [9]; assert(scratch[0] == 9); assert(saved.bytes[39999] == 7); print("defer=", saved.n); }
  if early { return saved.n; } total += saved.n;
 }
 return total;
}
fn main() {
 var a: Big[2] = [Big { bytes: [7; 40000], n: 3 }, Big { bytes: [7; 40000], n: 4 }];
 assert(check(a, true) == 3); assert(check(a, false) == 7);
 for &e, i in a { defer { print("loop=", e.n); } if i == 0 { continue; } break; }
 print("cleanup");
}
