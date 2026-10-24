// error: bench results must be fixed-width integers, bool, f32 or f64
bench "bad" fn bad() -> SharedAtomicU32 { abort("never"); }
fn main() {}
