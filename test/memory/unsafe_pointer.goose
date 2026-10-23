// no-jit runtime-debug: TinyCC cannot lower the alignment of pointer typedefs.
// These are real libc objects; no application allocation/read/write helpers.
extern fn unsafe_test_malloc(n: u64) -> UnsafePtr = "malloc";
extern fn unsafe_test_free(p: UnsafePtr) = "free";

fn check_scalar<T>(p: UnsafePtr, value: T) {
    unsafe_store<T>(p, value, false);
    assert(unsafe_load<T>(p, false) == value);
    unsafe_store<T>(p, value, true);
    assert(unsafe_load<T>(p, true) == value);
}
fn main() {
    let p = unsafe_test_malloc(64);
    assert(unsafe_handle_from_ptr(p) != 0);
    let h = unsafe_handle_from_ptr(p);
    let roundtrip = unsafe_ptr_from_handle(h);
    assert(unsafe_handle_from_ptr(roundtrip) == h);
    let q = unsafe_ptr_add(roundtrip, 1); // Deliberately unaligned.
    assert(unsafe_handle_from_ptr(q) == h + 1);
    assert(unsafe_handle_from_ptr(unsafe_ptr_add(q, -1)) == h);
    assert(unsafe_handle_from_ptr(unsafe_ptr_add(p, 0)) == h);
    check_scalar<u8>(q, 255);
    check_scalar<u16>(q, 65535);
    check_scalar<u32>(q, 4294967295);
    check_scalar<u64>(q, 18446744073709551615);
    check_scalar<i8>(q, -128);
    check_scalar<i16>(q, -32768);
    check_scalar<i32>(q, -2147483648);
    check_scalar<i64>(q, -9223372036854775808);
    unsafe_store<u64>(q, 72623859790382856, true);
    assert(unsafe_load<u8>(q, false) == 1);
    assert(unsafe_load<u8>(unsafe_ptr_add(q, 7), false) == 8);
    assert(unsafe_load<u64>(q, false) == 578437695752307201);
    unsafe_store<u16>(q, 4660, false);
    assert(unsafe_load<u8>(q, true) == 52);
    assert(unsafe_load<u16>(q, true) == 13330);
    assert(unsafe_handle_from_ptr(unsafe_ptr_from_handle(0)) == 0);
    unsafe_test_free(p);
    print("unsafe pointer ok");
}
