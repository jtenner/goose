struct Aligned { align(64) value: u32 }
struct Wrapper<T> { value: T }
struct Pair { a: Wrapper<u32>, b: Wrapper<Aligned> }
// error: aligned values are unsupported in channels
fn main() { let ch = channel<Pair>(); }
