struct Huge { bytes: u64[576460752303423488] }
fn main() { var h: Huge = default<Huge>(); print(h.bytes[0]); }
