fn invoke<F>(n: i64) { F(n); }
fn main() { invoke(7) { n: i64 => var local: i64 = n + 1; print(local); }; }
