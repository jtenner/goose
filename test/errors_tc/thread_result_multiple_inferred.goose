// error: thread_fn work may return at most one value
thread_fn work() { return 1, 2; }

fn main() { thread_spawn_join(work); }
