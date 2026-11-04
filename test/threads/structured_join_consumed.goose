thread_fn value() -> i64 { 42 }

fn main() {
    let worker = thread_spawn_join(value);
    let value, ok = thread_join(worker);
    assert(value == 42 && ok);
    thread_join(worker);
}
