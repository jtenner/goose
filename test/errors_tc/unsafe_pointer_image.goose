// error: native capabilities cannot be serialized
fn main() { let p: UnsafePtr[>..] = []; let image = to_bytes(p); }
