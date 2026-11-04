fn main() {
    let pointer, ok = qpoll<SharedPointer<i64>>();
    assert(!ok);
    shared_pointer_release(pointer);
}
