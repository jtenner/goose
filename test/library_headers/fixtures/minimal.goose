struct Box { token: SharedAtomicU32 }
recursive fn ident<T>(v: T) -> T { v }
export fn api() -> u32 {
    let owner, ok = shared_alloc(16); assert(ok);
    let t = shared_atomic_u32(owner, 0, 42);
    let b = ident(Box { token: t });
    let result = atomic_load(b.token, "Acquire");
    assert(shared_close(owner));
    result
}
