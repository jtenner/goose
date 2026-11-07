struct S { x: i64 = 7 }
fn main() { var a: S[1] = [S { x: 1 }]; for s in a { print(s.x); } }
