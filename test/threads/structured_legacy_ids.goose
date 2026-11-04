// Structured handles and legacy integer IDs share no API identity, whether
// the structured worker is live, joined normally or joined after an abort.
thread_fn blocked(ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    if ok { value } else { 0 }
}

thread_fn value() -> i64 { 42 }
thread_fn failed() -> i64 { abort("structured id failure") }
thread_fn legacy_wait(id: i64) { thread_wait(id); }

fn legacy_rejects(id: i64) {
    let waiter = thread_spawn_contained(legacy_wait, id);
    var why: u8[>..] = [];
    assert(!thread_wait(waiter, why));
    let want = "thread_wait on a structured worker id";
    assert(why.len > want.len && why[..want.len] == want);
}

thread_fn cancel_plain() -> i64 {
    let child = thread_spawn_join(value);
    thread_cancel(child);
    0
}

fn main() {
    let ch = channel<i64>();
    let live = thread_spawn_join(blocked, ch);       // worker id 0
    legacy_rejects(0);                              // waiter id 1
    assert(channel_send(ch, 7));
    let live_value, live_ok = thread_join(live);
    assert(live_value == 7 && live_ok);

    let done = thread_spawn_join(value);             // worker id 2
    let done_value, done_ok = thread_join(done);
    assert(done_value == 42 && done_ok);
    legacy_rejects(2);                              // waiter id 3

    let aborted = thread_spawn_contained_join(failed); // worker id 4
    var abort_why: u8[>..] = [];
    let abort_value, abort_ok = thread_join(aborted, abort_why);
    assert(abort_value == 0 && !abort_ok);
    legacy_rejects(4);                              // waiter id 5

    // A non-contained structured child cannot be cancelled. Its diagnostic
    // must end before the location suffix, without an embedded NUL byte.
    let parent = thread_spawn_contained_join(cancel_plain); // worker id 6, child id 7
    var cancel_why: u8[>..] = [];
    let parent_value, parent_ok = thread_join(parent, cancel_why);
    assert(parent_value == 0 && !parent_ok);
    let cancel = "only a structured contained worker can be cancelled";
    assert(cancel_why.len > cancel.len && cancel_why[..cancel.len] == cancel &&
           cancel_why[cancel.len] != 0);
    print("structured ids and diagnostics stay distinct");
}
