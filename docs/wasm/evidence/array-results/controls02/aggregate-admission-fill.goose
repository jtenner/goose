struct S { x: i64 = 7 }
fn main() { var s: S = S { x: 9 }; var a: S[2] = [s; 2]; print(a[1].x); }
