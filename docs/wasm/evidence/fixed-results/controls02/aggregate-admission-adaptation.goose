struct S { x: i64 = 7 }
fn main() { var a: S[1] = [S { x: 1 }]; var b: S[..2] = a; print(b[0].x); }
