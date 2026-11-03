fn main() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(7);
    assert(ok);
    let alias = pointer;
    shared_pointer_release(pointer);
    print(shared_pointer_copy(alias));
}
