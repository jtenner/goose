// error: thread_fn parameters must be flat
struct Raw { p: UnsafePtr }
thread_fn worker(p: Raw) {}
fn main() {}
