// Structured results and independent first-class channels (§11.2).
thread_fn square(n: i64) -> i64 { n * n }

thread_fn send(ch: Channel<i64>, value: i64) -> i64 {
    assert(channel_send(ch, value));
    value + 1
}

thread_fn make_bytes(n: i64) -> u8[>..] {
    var bytes: u8[>..] = [];
    for i in n { bytes.push((i + 1) as u8); }
    bytes
}

thread_fn blocked_send(ch: Channel<i64>) -> i64 {
    let sent = channel_send(ch, 2);
    assert(thread_cancelled());
    if sent { 1 } else { 0 }
}

thread_fn fail_result() -> i64 { abort("structured failure") }

struct LargeResult { prefix: u8, values: i64[40] }
thread_fn large_result() -> LargeResult { LargeResult { 9, [6; 40] } }

fn main() {
    let a = channel<i64>(1);
    let b = channel<i64>(1);
    let worker = thread_spawn_join(square, 7);
    let value, ok = thread_join(worker);
    print(value, " ", ok);

    assert(channel_try_send(b, 20));
    let sender = thread_spawn_contained_join(send, a, 10);
    let next, joined = thread_join(sender);
    print(channel_wait_any(a, b));
    let bv, bok = channel_receive(b);
    let av, aok = channel_receive(a);
    print(bv, " ", bok, " ", av, " ", aok, " ", next, " ", joined);
    print(channel_close(a), " ", channel_close(a));
    let empty, open = channel_receive(a);
    print(empty, " ", open);

    let bytes = channel<u8[>..]>(1);
    assert(channel_send(bytes, [7, 8, 9]));
    let packet, packet_ok = channel_receive(bytes);
    let maker = thread_spawn_join(make_bytes, 4);
    let made, made_ok = thread_join(maker);
    print(packet.len, " ", packet[1], " ", packet_ok, " ", made.len, " ", made[3], " ", made_ok);

    let full = channel<i64>(1);
    assert(channel_send(full, 1));
    let blocked = thread_spawn_contained_join(blocked_send, full);
    assert(thread_cancel(blocked));
    let cancelled, cancelled_ok = thread_join(blocked);
    print(cancelled, " ", cancelled_ok);

    let failed = thread_spawn_contained_join(fail_result);
    var why: u8[>..] = [];
    let failed_value, failed_ok = thread_join(failed, why);
    print(failed_value, " ", failed_ok, " ", why.len > 0);
    let large = thread_spawn_join(large_result);
    let large_value, large_ok = thread_join(large);
    print(large_value.prefix, " ", large_value.values[39], " ", large_ok);
}
