// error: invalid memory order for atomic store
fn main() { unsafe_atomic_store<u64>(0, 1, "Acquire"); }
