// error: expected a value of type u64
fn main() { let o, ok = shared_alloc(8); let v = shared_view(o, 0, 8); unsafe_ptr_from_handle(v); }
