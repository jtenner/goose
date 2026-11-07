struct S { x: i64 = 7 }
fn main() { var a: S[1][1] = [[S { x: 1 }]]; print(a[0][0].x); }
