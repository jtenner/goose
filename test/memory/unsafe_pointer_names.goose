// no-jit: UnsafePtr requires packed pointer typedef support.
import unsafe_pointer_ns.types;
fn identity<UnsafePtr>(x: UnsafePtr) -> UnsafePtr { x }
fn main() {
    let value = rawtypes::UnsafePtr { 17 };
    assert(rawtypes::local_value(value) == 17);
    assert(identity<i64>(31) == 31);
    let native: ::UnsafePtr = unsafe_ptr_from_handle(0);
    assert(rawtypes::root_handle(native) == 0);
    print("unsafe pointer names ok");
}
