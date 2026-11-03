import simd_vectors;

// error: explicit vectors have no public C ABI
export fn echo(v: f32x4) -> f32x4 { return v; }

fn main() {}
