// error: as requires a numeric source, got ::UnsafePtr
fn main() { let h = unsafe_ptr_from_handle(0) as u64; }
