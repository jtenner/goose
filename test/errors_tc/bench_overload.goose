// error: bench key cannot share an overload set
bench "x" fn bad() -> i64 { 1 }
fn bad(x: i64) -> i64 { x }
fn main() {}
