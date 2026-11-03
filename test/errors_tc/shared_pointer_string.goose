// error: SharedPointer value type must be recursively fixed and flat
fn main() { shared_pointer_alloc<u8[:]>("not flat"); }
