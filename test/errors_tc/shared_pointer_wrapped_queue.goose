// error: queue elements must be flat
struct Wrapped { pointer: SharedPointer<i64> }
fn main() {
    let pointer, owner, ok = shared_pointer_alloc<i64>(1);
    qput(Wrapped { pointer: pointer });
}
