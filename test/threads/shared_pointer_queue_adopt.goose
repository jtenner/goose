fn main() {
    let polled, poll_owner, poll_ok = shared_pointer_alloc<i64>(7);
    assert(poll_ok && qput(polled));
    let from_poll, got_poll = qpoll<SharedPointer<i64>>();
    assert(got_poll && shared_pointer_copy(from_poll) == 7);
    shared_pointer_release(from_poll);
    assert(shared_close(poll_owner));

    let waited, wait_owner, wait_ok = shared_pointer_alloc<i64>(9);
    assert(wait_ok && qput(waited));
    let from_wait = qget<SharedPointer<i64>>();
    assert(shared_pointer_copy(from_wait) == 9);
    shared_pointer_release(from_wait);
    assert(shared_close(wait_owner));

    let empty, got_empty = qpoll<SharedPointer<i64>>();
    assert(!got_empty);
    print("adopted");
}
