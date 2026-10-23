// error: const
fn main() { let o, ok = shared_alloc(64); let a = shared_borrow(shared_view(o, 0, 64)); memory_read_bytes(a, 0, "immutable"); }
