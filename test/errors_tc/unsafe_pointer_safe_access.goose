// error: requires UnsafePtr
fn main() { let o, ok = shared_alloc(8); let v = shared_view(o, 0, 8); let a = shared_borrow(v); unsafe_load<u8>(a, false); }
