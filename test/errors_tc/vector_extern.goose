import simd_vectors;

// error: explicit vectors have no public C ABI
extern fn take(v: f32x4);

fn main() {}
