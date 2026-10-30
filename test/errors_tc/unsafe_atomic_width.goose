// error: unsafe atomic type must be u32 or u64
fn main() { unsafe_atomic_load<i32>(0, "Relaxed"); }
