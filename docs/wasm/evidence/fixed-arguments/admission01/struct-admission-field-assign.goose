struct S { x: i64 }
struct Outer { s: S }
fn main() { var a: Outer = Outer { s: S { x: 1 } }; var b: S = S { x: 2 }; a.s = b; print(a.s.x); }
