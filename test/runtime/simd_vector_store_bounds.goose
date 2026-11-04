import simd_vectors;
fn main() {
    var xs: u32[5] = [1, 2, 3, 4, 5];
    print(xs);
    vector_store_u32x4(xs, 2, splat_u32x4(9));
}
