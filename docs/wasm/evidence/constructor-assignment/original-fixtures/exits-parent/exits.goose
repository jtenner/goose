struct S { a: i64, b: i64 }
var target: S = S { a: 1, b: 2 };
fn main() {
 for i in 4 {
  defer { print("outer"); }
  target = S { a: target.a + 1, b: { defer { print("inner"); } if i == 1 { continue; } if i == 3 { break; } 7 } };
  print("step");
 }
 assert(target.a == 3); assert(target.b == 7); print("exits");
}
