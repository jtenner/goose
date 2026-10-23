// error: expected a value of type i64
fn main() { let offset: u64 = 1; unsafe_ptr_add(unsafe_ptr_from_handle(0), offset); }
