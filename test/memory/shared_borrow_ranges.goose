// no-jit
struct RangeReady { n: i64 }
struct RangeContinue { n: i64 }
thread_fn ranged(v: SharedView, offset: i64) {
    let a = shared_borrow(v, offset, 8);
    qput(RangeReady { n: 1 }); qget<RangeContinue>();
    memory_write<u64>(a, 0, offset as u64, false);
    shared_release(a);
}
thread_fn bad_range(v: SharedView, kind: i64) {
    if kind == 0 { shared_borrow(v, -1, 1); }
    if kind == 1 { shared_borrow(v, 63, 2); }
    if kind == 2 { shared_borrow(v, 0, 18446744073709551615); }
    if kind == 3 { shared_view(v, 63, 2); }
}
fn main() {
    let o, ok = shared_alloc(64); assert(ok);
    let v = shared_view(o, 0, 64);
    var ids: i64[>..] = [];
    for i in 4 { ids.push(thread_spawn(ranged, v, i * 8)); }
    for i in 4 { qget<RangeReady>(); }
    let independent = shared_borrow(v, 40, 8);
    memory_write<u64>(independent, 0, 99, false); shared_release(independent);
    for i in 4 { qput(RangeContinue { n: 1 }); }
    for id in ids { assert(thread_wait(id)); }
    for i in 4 {
        let a = shared_borrow(v, i * 8, 8);
        assert(memory_read<u64>(a, 0, false) == (i * 8) as u64); shared_release(a);
    }
    for i in 4 { assert(!thread_wait(thread_spawn_contained(bad_range, v, i))); }
    assert(shared_close(o)); print("shared borrow ranges ok");
}
