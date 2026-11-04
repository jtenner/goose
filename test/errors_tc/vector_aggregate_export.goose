import simd_vectors;

struct Wrapper { vector: u32x4 }

// error: explicit vectors have no public C ABI
export fn echo(value: Wrapper) -> Wrapper { return value; }

fn main() {}
