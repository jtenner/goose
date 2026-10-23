struct PrivateNative<T> { prefix: u8, token: T, tail: u16 }
struct PrivateNested<T> { values: PrivateNative<T>[1] }
recursive fn ident<T>(v: T) -> T { v }
export fn api() -> u32 {
    let owner, ok = shared_alloc(32); assert(ok);
    let o = ident(PrivateNested<SharedOwner> { [PrivateNative { 1, owner, 2 }] });
    assert(shared_size(o.values[0].token) == 32);
    let v = ident(PrivateNested<SharedView> {
        [PrivateNative { 3, shared_view(o.values[0].token, 16, 16), 4 }]
    });
    assert(shared_size(v.values[0].token) == 16);
    let a = ident(PrivateNested<SharedAccess> {
        [PrivateNative { 5, shared_borrow(v.values[0].token), 6 }]
    });
    memory_write<u32>(a.values[0].token, 1, 42, false);
    assert(memory_read<u32>(a.values[0].token, 1, false) == 42);
    shared_release(a.values[0].token);
    let x = ident(PrivateNested<SharedAtomicU32> {
        [PrivateNative { 7, shared_atomic_u32(owner, 0, 42), 8 }]
    });
    let y = ident(PrivateNested<SharedAtomicU64> {
        [PrivateNative { 9, shared_atomic_u64(owner, 8, 55), 10 }]
    });
    assert(atomic_load(y.values[0].token, "Acquire") == 55);
    let result = atomic_load(x.values[0].token, "Acquire");
    assert(shared_close(o.values[0].token));
    result
}
