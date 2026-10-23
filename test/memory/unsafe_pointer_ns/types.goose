namespace rawtypes;
struct UnsafePtr { value: i64 }
fn local_value(p: UnsafePtr) -> i64 { p.value }
fn root_handle(p: ::UnsafePtr) -> u64 { unsafe_handle_from_ptr(p) }
