// error: native capabilities cannot be serialized
fn main() { let p = from_bytes<UnsafePtr[>..]>(""); }
