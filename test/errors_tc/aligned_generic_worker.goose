struct Aligned { align(64) x: u32 }
struct Wrapper<T> { value: T }
struct Pair { first: Wrapper<u32>, second: Wrapper<Aligned> }
// error: aligned values are unsupported in worker argument packets
thread_fn worker(value: Pair) {}
fn main() { let value: Pair; thread_spawn(worker, value); }
