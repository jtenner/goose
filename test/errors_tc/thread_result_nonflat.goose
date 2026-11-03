// error: thread_fn result must be flat
thread_fn bad() -> u8[:] { "x" }
fn main() { thread_spawn_join(bad); }
