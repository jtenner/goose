import simd_vectors;
fn main() {
    let xs: f32[4] = [1.0, 2.0, 3.0, 4.0];
    print(vector_load_f32x4(xs, 1));
}
