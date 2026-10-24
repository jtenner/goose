// error: bench function takes no parameters
bench "x" fn bad(x: i64 = 1) -> i64 { x }
fn main() {}
