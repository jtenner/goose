// error: thread_join requires Thread<T>
thread_fn worker() {}
fn main() { thread_join(thread_spawn(worker)); }
