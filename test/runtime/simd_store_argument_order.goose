import simd_vectors;
fn value() -> u32x4 { print(123); return [1, 2, 3, 4]; }
fn main() {
    var xs: u32[2] = [0, 0];
    __simd_store<u32x4>(xs, 0, value());
}
