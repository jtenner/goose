struct S { x: i64 }
fn invoke<F>(a: S[1]&) { F(copy(a)); }
fn main() { var a: S[1] = [S { x: 1 }]; invoke(a) { p: S[1] => print(p[0].x); }; }
