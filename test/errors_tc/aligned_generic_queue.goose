struct Aligned { align(64) x: u32 }
struct Wrapper<T> { value: T }
struct Pair { first: Wrapper<u32>, second: Wrapper<Aligned> }
// error: aligned values are unsupported in queues
fn main() {
    let value, ok = qpoll<Pair>();
}
