struct S { x: i64 = 7 }
fn main() { var a: S[..3] = [S { x: 1 }]; var s: S = S { x: 2 }; a.push(s); print(a.len); }
