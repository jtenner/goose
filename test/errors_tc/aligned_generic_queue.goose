struct Aligned { align(64) x: u32 }
struct Wrapper<T> { value: T }
struct Pair { first: Wrapper<u32>, second: Wrapper<Aligned> }
fn main() {
    // error: aligned values are unsupported in queues
    let value, ok = qpoll<Pair>();
}
