// error: unsafe scalar type must be i/u8/16/32/64
fn main() { unsafe_load<f32>(unsafe_ptr_from_handle(0), false); }
