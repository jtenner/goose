// error: thread_fn parameters must be flat
// error: thread_fn parameters must be flat
thread_fn value() -> i64 { 1 }
thread_fn wrong_owner(handle: Thread<i64>) { thread_join(handle); }
fn main() {
    let handle = thread_spawn_join(value);
    thread_wait(thread_spawn(wrong_owner, handle));
}
