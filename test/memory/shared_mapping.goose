// no-jit
import os;
struct MapReady { n: i64 }
struct MapContinue { n: i64 }
thread_fn mapped_reader(v: SharedView) {
    let a = shared_borrow(shared_view(v, 1, 4));
    qput(MapReady { n: 1 });
    qget<MapContinue>();
    assert(memory_read<u8>(a, 0, false) == 98);
    shared_release(a);
}
thread_fn readonly_write(v: SharedView) {
    let a = shared_borrow(v);
    memory_write<u8>(a, 0, 0, false);
}
thread_fn readonly_atomic(path: u8[8]) {
    let o, ok = shared_map_readonly(path, 8); assert(ok);
    shared_atomic_u32(o, 0, 0);
}
fn main() {
    let path = "gsmaptmp";
    assert(write_file(path, "abcdefgh"));
    let missing, no = shared_map_readonly("gs_no_such_mapping_987654", 8); assert(!no);
    let large, beyond = shared_map_readonly(path, 9); assert(!beyond);
    let empty, zero = shared_map_readonly(path, 0); assert(!zero);
    let o, ok = shared_map_readonly(path, 8); assert(ok && shared_size(o) == 8);
    let v = shared_view(o, 0, 8);
    var ids: i64[>..] = [];
    for i in 4 { ids.push(thread_spawn(mapped_reader, v)); }
    for i in 4 { qget<MapReady>(); }
    assert(!shared_close(o));
    for i in 4 { qput(MapContinue { n: 1 }); }
    for id in ids { assert(thread_wait(id)); }
    let a = shared_borrow(v);
    var out: u8[8] = default<u8[8]>();
    memory_read_bytes(a, 0, out);
    assert(out == "abcdefgh");
    shared_release(a);
    assert(!thread_wait(thread_spawn_contained(readonly_write, v)));
    assert(!thread_wait(thread_spawn_contained(readonly_atomic, [103, 115, 109, 97, 112, 116, 109, 112])));
    let supported, applied = shared_page_advice(v, 0, 8, "Sequential");
    assert(!applied || supported);
    assert(shared_close(o));
    let anon, yes = shared_alloc(64); assert(yes);
    let av = shared_view(anon, 0, 64); let aa = shared_borrow(av);
    memory_write_bytes(aa, 1, "hello");
    var bytes: u8[5] = default<u8[5]>(); memory_read_bytes(aa, 1, bytes);
    assert(bytes == "hello"); shared_release(aa);
    let can_discard, discarded = shared_page_advice(av, 0, 64, "DontNeed");
    assert(!discarded); // Anonymous live bytes must never be destructively discarded.
    let check = shared_borrow(av); assert(memory_read<u8>(check, 1, false) == 104); shared_release(check);
    assert(shared_close(anon)); assert(delete_file(path));
    print("shared mapping ok");
}
