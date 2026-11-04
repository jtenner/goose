struct Aligned { tag: u8, align(16) value: u32 }

// error: aligned element types are unsupported in non-fixed arrays
fn main() { let values: Aligned[] = []; }
