// Dropping a structured contained handle cannot leave completion state or a
// blocked child behind: main's containing-scope cleanup cancels and joins it.
thread_fn blocked(ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    if ok { value } else { 0 }
}

fn main() {
    let ch = channel<i64>();
    thread_spawn_contained_join(blocked, ch);
}
