struct Aligned { align(64) value: u32 }
// error: aligned struct fields require fixed packed storage
struct Wrapper<T, Tail> { tag: u8, value: T, tail: Tail }
fn main() { let value: Wrapper<Aligned, u8[>..]>; }
