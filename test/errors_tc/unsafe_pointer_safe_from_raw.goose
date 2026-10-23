// error: as requires a numeric source, got UnsafePtr
fn main() { let p = unsafe_ptr_from_handle(0) as SharedView; }
