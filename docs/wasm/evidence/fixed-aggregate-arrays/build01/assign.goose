struct S { x: i64 = 7 }
fn main() { var a: S[1] = [S { x: 1 }]; var b: S = S { x: 2 }; a[0] = b; print(a[0].x); }
