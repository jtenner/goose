// Cancellation executes when discarded, beats queued data, is inherited by
// children registered afterward, and reaches descendants before cleanup joins.
thread_fn blocked(ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    if ok { value } else { 0 }
}

thread_fn inherit_child() -> i64 { if thread_cancelled() { 1 } else { 0 } }
thread_fn inherit_parent() -> i64 {
    while !thread_cancelled() {}
    let child = thread_spawn_contained_join(inherit_child);
    let inherited, ok = thread_join(child);
    assert(ok);
    inherited
}

thread_fn queued(ch: Channel<i64>) -> i64 {
    while !thread_cancelled() {}
    let value, ok = channel_receive(ch);
    if ok { value } else { 0 }
}

thread_fn descendant(ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    if ok { value } else { 0 }
}
thread_fn parent(ch: Channel<i64>) -> i64 {
    let child = thread_spawn_contained_join(descendant, ch);
    assert(qput(true));
    let value, ok = thread_join(child);
    value
}

fn main() {
    let empty = channel<i64>();
    let discard = thread_spawn_contained_join(blocked, empty);
    thread_cancel(discard);
    let cancelled, cancelled_ok = thread_join(discard);
    print(cancelled, " ", cancelled_ok);

    let inherited = thread_spawn_contained_join(inherit_parent);
    assert(thread_cancel(inherited));
    let inherited_value, inherited_ok = thread_join(inherited);
    print(inherited_value, " ", inherited_ok);

    let with_value = channel<i64>();
    assert(channel_send(with_value, 42));
    let queued_worker = thread_spawn_contained_join(queued, with_value);
    assert(thread_cancel(queued_worker));
    let queued_value, queued_ok = thread_join(queued_worker);
    let preserved, preserved_ok = channel_try_receive(with_value);
    print(queued_value, " ", queued_ok, " ", preserved, " ", preserved_ok);

    let descendants = channel<i64>();
    thread_spawn_contained_join(parent, descendants);
    assert(qget<bool>());
}
