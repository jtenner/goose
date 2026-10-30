// error: memory order must be a compile-time string
fn load(order: u8[:]) -> u32 { unsafe_atomic_load<u32>(0, order) }
fn main() { print(load("Relaxed")); }
