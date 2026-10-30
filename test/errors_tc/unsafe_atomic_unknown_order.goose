// error: unknown memory order
fn main() { unsafe_atomic_load<u64>(0, "consume"); }
