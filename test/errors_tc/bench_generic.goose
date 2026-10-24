// error: bench function cannot be generic
bench "x" fn bad<T>() -> i64 { 1 }
fn main() {}
