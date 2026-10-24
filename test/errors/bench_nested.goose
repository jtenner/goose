// error: bench requires a top-level function
fn main() { bench "x" fn bad() -> i64 { 1 } }
