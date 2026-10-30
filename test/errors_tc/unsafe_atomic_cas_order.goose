// error: invalid compare_exchange failure order
fn main() { unsafe_atomic_compare_exchange<u32>(0, 0, 1, "Release", "Acquire"); }
