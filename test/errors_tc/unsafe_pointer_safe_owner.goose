// error: requires UnsafePtr
fn main() { let o, ok = shared_alloc(8); unsafe_handle_from_ptr(o); }
