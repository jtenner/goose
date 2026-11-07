struct S { x: i64 = 7 }
fn main() { var a: S[..3] = [S { x: 1 }]; a.pop(); print(a.len); }
