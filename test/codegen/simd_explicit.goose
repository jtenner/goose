// Explicit SIMD vector aliases retain scalar semantics on every backend.

import simd_vectors;
import std;

fn main() {
    let a = splat_f32x4(2.0);
    let b: f32x4 = [1.0, 2.0, 3.0, 4.0];
    let c = a * b + b;
    print(c);

    var xs: f32[>..] = [10.0, 20.0, 30.0, 40.0, 50.0];
    let d = vector_load_f32x4(xs, 1);
    vector_store_f32x4(xs, 0, d);
    print(xs);

    let u = splat_u32x4(3);
    let v: u32x4 = [1, 2, 3, 4];
    print(u + v, " ", u * v);
    print(shuffle_u32x4(v, 3, 1, 1, 0));
    let si: i32x4 = [2147483647, -2147483648, -2, 7];
    let sj: i32x4 = [1, -1, 3, -4];
    print(si + sj, " ", si * sj, " ", si / sj);
}
