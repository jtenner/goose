fn main() {
    let owner, ok = shared_alloc(32);
    assert(ok);
    let access = shared_borrow(shared_view(owner, 8, 8));
    shared_pointer_alloc<i64>(owner, 8, 1);
}
