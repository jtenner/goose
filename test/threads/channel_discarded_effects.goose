// Effectful channel operations execute even when their result is discarded.
import os;

thread_fn delayed_send(ch: Channel<i64>) {
    sleep_ms(20);
    assert(channel_send(ch, 7));
}

fn main() {
    let closed = channel<i64>();
    channel_close(closed);
    print(channel_close(closed));

    let ready = channel<i64>();
    let sender = thread_spawn(delayed_send, ready);
    channel_wait_any(ready);
    let value, ok = channel_try_receive(ready);
    assert(thread_wait(sender));
    print(value, " ", ok);
}
