// error: unsafe scalar type must be i/u8/16/32/64
fn main() { unsafe_store<bool>(unsafe_ptr_from_handle(0), false, false); }
