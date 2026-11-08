struct S { x: i64 }
fn main() { var a: S = S { x: 1 }; var b: S = S { x: 2 }; var refs: S&[1] = [a]; refs[0] = b; print(a.x); }
