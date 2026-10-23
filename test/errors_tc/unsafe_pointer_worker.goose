// error: thread_fn parameters must be flat
thread_fn worker(p: UnsafePtr) {}
fn main() { thread_spawn(worker, unsafe_ptr_from_handle(0)); }
