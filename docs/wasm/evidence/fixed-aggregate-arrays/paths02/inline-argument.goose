struct S { x: i64 }
inline fn read(a: S[1]) -> i64 { a[0].x }
fn main() { var a: S[1] = [S { x: 1 }]; print(read(a)); }
