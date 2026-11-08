struct S { x: i64 = 7 }
fn main() { var a: S[1] = [S { x: 1 }]; var b: S[1] = [S { x: 1 }]; print(a == b); }
