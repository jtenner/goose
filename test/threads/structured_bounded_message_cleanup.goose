thread_fn fail_join() -> i64 { abort("diagnostic"); }
thread_fn fail_wait() { abort("diagnostic"); }

thread_fn bounded_join_parent() -> i64 {
    var msg: u8[..1] = [];
    let value, ok = thread_join(thread_spawn_contained_join(fail_join), msg);
    assert(ok);
    value
}

thread_fn bounded_wait_parent() -> i64 {
    var msg: u8[..1] = [];
    assert(thread_wait(thread_spawn_contained(fail_wait), msg));
    0
}

fn main() {
    for i in 10 {
        let join_value, join_ok = thread_join(
            thread_spawn_contained_join(bounded_join_parent));
        assert(!join_ok);
        let wait_value, wait_ok = thread_join(
            thread_spawn_contained_join(bounded_wait_parent));
        assert(!wait_ok);
    }

    // A bounded destination with enough room takes and releases each message
    // normally; the overflow path above releases before its contained abort.
    var join_msg: u8[..512] = [];
    let join_value, join_ok = thread_join(thread_spawn_contained_join(fail_join), join_msg);
    assert(!join_ok && join_msg.len > 0);
    var wait_msg: u8[..512] = [];
    assert(!thread_wait(thread_spawn_contained(fail_wait), wait_msg));
    assert(wait_msg.len > 0);
    print("bounded message parents contained");
}
