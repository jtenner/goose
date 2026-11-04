// error: aligned struct fields require fixed packed storage
struct Bad { tag: u8, align(64) value: u32, tail: u8[] }
fn main() { let value = Bad { 1, 7, [1, 2] }; }
