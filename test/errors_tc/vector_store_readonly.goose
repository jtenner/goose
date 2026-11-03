import simd_vectors;

fn main() {
    let xs: const f32[4] = [1.0, 2.0, 3.0, 4.0];
// error: cannot assign through this path
    vector_store_f32x4(xs, 0, splat_f32x4(1.0));
}
