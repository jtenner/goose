struct PrivateRaw { prefix: u8, pointer: UnsafePtr }
recursive fn ident<T>(v: T) -> T { v }
export fn api() -> u32 {
    let p = ident(PrivateRaw { 1, unsafe_ptr_from_handle(42) });
    unsafe_handle_from_ptr(p.pointer) as u32
}
