// error: bench results must be fixed-width integers, bool, f32 or f64
bench "x" fn bad() { "string" }
fn main() {}
