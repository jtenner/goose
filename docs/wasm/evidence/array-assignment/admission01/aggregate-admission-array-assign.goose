struct S { x: i64 }
fn main() { var a: S[1] = [S { x: 1 }]; var b: S[1] = [S { x: 2 }]; a = b; print(a[0].x); }
