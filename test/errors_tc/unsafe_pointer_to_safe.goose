// error: requires SharedAccess
fn main() { memory_read<u8>(unsafe_ptr_from_handle(0), 0, false); }
