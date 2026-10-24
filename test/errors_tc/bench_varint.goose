// error: varint is a storage type: only fields and array elements
bench "bad" fn bad() -> varint { abort("never"); }
fn main() {}
