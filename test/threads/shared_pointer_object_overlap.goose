fn main() {
    let owner, ok = shared_alloc(32);
    assert(ok);
    let pointer, pointer_ok = shared_pointer_alloc<i64>(owner, 8, 1);
    assert(pointer_ok);
    shared_pointer_alloc<i64>(owner, 8, 2);
}
