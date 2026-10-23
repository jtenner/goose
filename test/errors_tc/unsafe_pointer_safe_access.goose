// error: requires UnsafePtr
fn main() { unsafe_load<u8>(default<SharedAccess>(), false); }
