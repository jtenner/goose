// Persistent cancellation scopes cover descendants registered after a request,
// including through non-contained structured workers, but not legacy workers.
thread_fn leaf() -> i64 { if thread_cancelled() { 1 } else { 0 } }

thread_fn structured_middle(start: bool) -> i64 {
    if start { assert(qget<u8>() == 1); }
    let child = thread_spawn_contained_join(leaf);
    let value, ok = thread_join(child);
    assert(ok);
    value
}

// The intermediary exists before its contained ancestor is cancelled.
thread_fn existing_root() -> i64 {
    let middle = thread_spawn_join(structured_middle, true);
    assert(qput(true));
    let value, ok = thread_join(middle);
    assert(ok);
    value
}

// The intermediary itself is registered after its ancestor is cancelled.
thread_fn later_root() -> i64 {
    while !thread_cancelled() {}
    let middle = thread_spawn_join(structured_middle, false);
    let value, ok = thread_join(middle);
    assert(ok);
    value
}

thread_fn legacy_middle() {
    let child = thread_spawn_contained_join(leaf);
    let value, ok = thread_join(child);
    assert(ok && value == 0);
}

thread_fn legacy_root() -> i64 {
    while !thread_cancelled() {}
    let middle = thread_spawn(legacy_middle);
    assert(thread_wait(middle));
    1
}

// Cancellation of this worker is the synchronization proving main cleanup has
// entered its persistent closing state before cleanup_middle registers leaf.
thread_fn cleanup_notifier(ch: Channel<i64>) -> i64 {
    let value, ok = channel_receive(ch);
    assert(!ok && thread_cancelled());
    let ready: u16 = 1;
    assert(qput(ready));
    value
}

thread_fn cleanup_middle() -> i64 {
    assert(qget<u16>() == 1);
    let child = thread_spawn_contained_join(leaf);
    let value, ok = thread_join(child);
    assert(ok && value == 1);
    value
}

fn main() {
    let existing = thread_spawn_contained_join(existing_root);
    assert(qget<bool>());
    assert(thread_cancel(existing));
    let start: u8 = 1;
    assert(qput(start));
    let existing_value, existing_ok = thread_join(existing);
    print(existing_value, " ", existing_ok);

    let later = thread_spawn_contained_join(later_root);
    assert(thread_cancel(later));
    let later_value, later_ok = thread_join(later);
    print(later_value, " ", later_ok);

    let legacy = thread_spawn_contained_join(legacy_root);
    assert(thread_cancel(legacy));
    let legacy_value, legacy_ok = thread_join(legacy);
    print(legacy_value, " ", legacy_ok);

    let blocked = channel<i64>();
    thread_spawn_join(cleanup_middle);
    thread_spawn_contained_join(cleanup_notifier, blocked);
}
