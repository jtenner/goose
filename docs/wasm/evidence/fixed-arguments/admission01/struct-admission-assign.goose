struct S { x: i64 }
fn main() { var a: S = S { x: 1 }; var b: S = S { x: 2 }; a = b; print(a.x); }
