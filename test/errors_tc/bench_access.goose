// error: bench results must be fixed-width integers, bool, f32 or f64
bench "bad" fn bad() -> SharedAccess { abort("never"); }
fn main() {}
