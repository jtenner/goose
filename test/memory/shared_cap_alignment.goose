// no-jit
// Capability values can occur at byte offset one in packed Goose storage.
// Their wrappers must tolerate this; descriptors and atomic cells stay aligned.
struct CapPacket {
    tag: u8,
    view: SharedView,
    a32: SharedAtomicU32,
    gap: u8,
    a64: SharedAtomicU64
}
fn view_of(p: CapPacket) -> SharedView { p.view }
fn handles(p: CapPacket) -> SharedAtomicU32, SharedAtomicU64 { return p.a32, p.a64; }
fn first(v: SharedView[:]) -> SharedView { v[0] }
thread_fn packed_worker(tag: u8, view: SharedView, a32: SharedAtomicU32, a64: SharedAtomicU64) {
    assert(tag == 9);
    assert(atomic_fetch_add(a32, 1, "Relaxed") == 0);
    assert(atomic_fetch_add(a64, 2, "Relaxed") == 0);
    let access = shared_borrow(view);
    memory_write<u64>(access, 1, 1234, true); shared_release(access);
}
fn main() {
    let owner, ok = shared_alloc(64); assert(ok);
    let v = shared_view(owner, 32, 16);
    let a32 = shared_atomic_u32(owner, 0, 0);
    let a64 = shared_atomic_u64(owner, 8, 0);
    let packet = CapPacket { tag: 9, view: v, a32: a32, gap: 1, a64: a64 };
    let views = [view_of(packet), v];
    let aa, bb = handles(packet);
    let small = [aa, a32]; let wide = [bb, a64];
    assert(thread_wait(thread_spawn(packed_worker, packet.tag, first(views), small[1], wide[1])));
    assert(atomic_load(packet.a32, "Acquire") == 1);
    assert(atomic_load(packet.a64, "Acquire") == 2);
    let access = shared_borrow(packet.view);
    assert(memory_read<u64>(access, 1, true) == 1234); shared_release(access);
    assert(shared_close(owner)); print("shared capability alignment ok");
}
