import simd_vectors;
fn main() {
    let xs: u32x4 = [1, 2, 3, 4];
    print(shuffle_u32x4(xs, 0, 1, 2, 4));
}
