// error: unsafe scalar access needs exactly one type argument
fn main() { unsafe_load(unsafe_ptr_from_handle(0), false); }
