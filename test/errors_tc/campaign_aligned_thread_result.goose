struct Aligned { align(64) value: u32 }
thread_fn worker() -> Aligned { Aligned { value: 7 } }
// error: aligned values are unsupported in worker result packets
fn main() { let handle = thread_spawn_join(worker); }
