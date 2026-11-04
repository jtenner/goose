fn main() {
    let owner, ok = shared_alloc(32);
    assert(ok);
    shared_atomic_u64(owner, 8, 0);
    shared_pointer_alloc<i64>(owner, 8, 1);
}
