// error: bench results must be fixed-width integers, bool, f32 or f64
struct S { x: i64 }
bench "x" fn bad() { S { x: 1 } }
fn main() {}
