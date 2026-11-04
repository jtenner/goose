thread_fn joined(ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    assert(!ok);
    42
}

thread_fn waited(ch: Channel<i64>) {
    let value, ok = channel_receive(ch);
    assert(!ok);
}

fn message(out: u8[>..]&, ch: Channel<i64>) -> u8[>..]& {
    assert(channel_close(ch));
    out
}

fn main() {
    var messages: u8[>..] = [];

    let join_ch = channel<i64>();
    let handle = thread_spawn_join(joined, join_ch);
    let value, joined = thread_join(handle, message(messages, join_ch));
    print(value, " ", joined);

    let wait_ch = channel<i64>();
    let id = thread_spawn(waited, wait_ch);
    print(thread_wait(id, message(messages, wait_ch)));
}
