struct S { x: i64 = 7 }
fn main() { var a: S[..3] = [S { x: 1 }]; var s: S = a.pop(); print(s.x); }
