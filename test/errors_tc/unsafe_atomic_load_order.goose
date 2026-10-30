// error: invalid memory order for atomic load
fn main() { unsafe_atomic_load<u32>(0, "Release"); }
