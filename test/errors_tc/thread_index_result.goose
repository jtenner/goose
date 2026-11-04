// error: cannot return between threads: it holds an index type
var items: i64[>..] = [];
thread_fn bad() -> u32 in items { 0 as u32 in items }
fn main() { thread_spawn_join(bad); }
