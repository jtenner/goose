struct S { x: i64 }
fn main() { var s: S = S { x: 7 }; var a: S[32] = [s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s]; print(a.len, ",", a[31].x); }
