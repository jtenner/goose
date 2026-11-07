struct S { n: i64 }
var target: S = S { n: 1 };
fn main() { for i in 4 { target = S { n: target.n + 1 }; print("step"); } assert(target.n == 5); print("loop"); }
