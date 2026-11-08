struct S { x: i64 }
inline fn read(s: S) -> i64 { s.x }
fn main() { var s: S = S { x: 1 }; print(read(s)); }
