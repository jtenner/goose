import simd_vectors;
fn main() {
    let v: u32x4 = [1, 2, 3, 4];
    print(shuffle_u32x4(v, 8, 0, 0, 0));
}
