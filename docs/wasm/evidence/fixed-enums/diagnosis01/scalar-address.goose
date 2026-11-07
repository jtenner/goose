recursive fn change(n: i64&) { n += 2; }
fn invoke<F>(n: i64) { F(n); }
fn main() { invoke(7) { n: i64 => var local: i64 = n; change(local); assert(local == 9); print(local); }; }
