thread_fn send(ch: Channel<i64>) -> i64 {
    for i in 10000 { assert(channel_send(ch, i)); }
    0
}

fn main() {
    let ch = channel<i64>(1);
    let worker = thread_spawn_join(send, ch);
    for i in 10000 {
        // A send can race between occurrences. Once any occurrence observes
        // readiness, the first identical argument is the required answer.
        assert(channel_wait_any(ch, ch, ch, ch) == 0);
        let value, ok = channel_receive(ch);
        assert(ok && value == i);
    }
    let result, joined = thread_join(worker);
    assert(joined && result == 0);

    let empty = channel<i64>(1);
    assert(channel_send(ch, 10000));
    assert(channel_wait_any(empty, ch, ch) == 1);
    print("duplicate wait-any chose its first occurrence");
}
