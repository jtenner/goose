struct S { x: i64 }
struct A { xs: u8[3] }
struct B { xs: u8[..4] }
fn main() { var a: A = A { xs: [1, 2, 3] }; var b: B = B { xs: a.xs }; print(b.xs[0]); }
