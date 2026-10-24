// error: bench results must be fixed-width integers, bool, f32 or f64
var x = 1;
bench "x" fn bad() -> i64& { x }
fn main() {}
