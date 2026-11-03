// Explicit fixed-width SIMD values (spec §7.12). These aliases deliberately
// retain the language's fixed-array representation: packed, byte-aligned,
// flat and available to scalar-only backends. The C backend recognizes the
// same shapes for its GS_VEC expression lowering.

type i8x16 = i8[16];
type i8x32 = i8[32];
type i8x64 = i8[64];
type u8x16 = u8[16];
type u8x32 = u8[32];
type u8x64 = u8[64];
type i16x8 = i16[8];
type i16x16 = i16[16];
type i16x32 = i16[32];
type u16x8 = u16[8];
type u16x16 = u16[16];
type u16x32 = u16[32];
type i32x4 = i32[4];
type i32x8 = i32[8];
type i32x16 = i32[16];
type u32x4 = u32[4];
type u32x8 = u32[8];
type u32x16 = u32[16];
type i64x2 = i64[2];
type i64x4 = i64[4];
type i64x8 = i64[8];
type u64x2 = u64[2];
type u64x4 = u64[4];
type u64x8 = u64[8];
type f32x4 = f32[4];
type f32x8 = f32[8];
type f32x16 = f32[16];
type f64x2 = f64[2];
type f64x4 = f64[4];
type f64x8 = f64[8];

fn splat_i8x16(x: i8) -> i8x16 { return [x; 16]; }
fn vector_load_i8x16(xs: const i8[:], first: i64) -> i8x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: i8x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i8x16(xs: i8[:], first: i64, v: i8x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_i8x32(x: i8) -> i8x32 { return [x; 32]; }
fn vector_load_i8x32(xs: const i8[:], first: i64) -> i8x32 {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    var r: i8x32 = [0; 32];
    for i in 32 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i8x32(xs: i8[:], first: i64, v: i8x32) {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    for i in 32 { xs[first + i] = v[i]; }
}
fn splat_i8x64(x: i8) -> i8x64 { return [x; 64]; }
fn vector_load_i8x64(xs: const i8[:], first: i64) -> i8x64 {
    assert(first >= 0 && xs.len >= 64 && first <= xs.len - 64);
    var r: i8x64 = [0; 64];
    for i in 64 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i8x64(xs: i8[:], first: i64, v: i8x64) {
    assert(first >= 0 && xs.len >= 64 && first <= xs.len - 64);
    for i in 64 { xs[first + i] = v[i]; }
}
fn splat_u8x16(x: u8) -> u8x16 { return [x; 16]; }
fn vector_load_u8x16(xs: const u8[:], first: i64) -> u8x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: u8x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u8x16(xs: u8[:], first: i64, v: u8x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_u8x32(x: u8) -> u8x32 { return [x; 32]; }
fn vector_load_u8x32(xs: const u8[:], first: i64) -> u8x32 {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    var r: u8x32 = [0; 32];
    for i in 32 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u8x32(xs: u8[:], first: i64, v: u8x32) {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    for i in 32 { xs[first + i] = v[i]; }
}
fn splat_u8x64(x: u8) -> u8x64 { return [x; 64]; }
fn vector_load_u8x64(xs: const u8[:], first: i64) -> u8x64 {
    assert(first >= 0 && xs.len >= 64 && first <= xs.len - 64);
    var r: u8x64 = [0; 64];
    for i in 64 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u8x64(xs: u8[:], first: i64, v: u8x64) {
    assert(first >= 0 && xs.len >= 64 && first <= xs.len - 64);
    for i in 64 { xs[first + i] = v[i]; }
}
fn splat_i16x8(x: i16) -> i16x8 { return [x; 8]; }
fn vector_load_i16x8(xs: const i16[:], first: i64) -> i16x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: i16x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i16x8(xs: i16[:], first: i64, v: i16x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_i16x16(x: i16) -> i16x16 { return [x; 16]; }
fn vector_load_i16x16(xs: const i16[:], first: i64) -> i16x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: i16x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i16x16(xs: i16[:], first: i64, v: i16x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_i16x32(x: i16) -> i16x32 { return [x; 32]; }
fn vector_load_i16x32(xs: const i16[:], first: i64) -> i16x32 {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    var r: i16x32 = [0; 32];
    for i in 32 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i16x32(xs: i16[:], first: i64, v: i16x32) {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    for i in 32 { xs[first + i] = v[i]; }
}
fn splat_u16x8(x: u16) -> u16x8 { return [x; 8]; }
fn vector_load_u16x8(xs: const u16[:], first: i64) -> u16x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: u16x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u16x8(xs: u16[:], first: i64, v: u16x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_u16x16(x: u16) -> u16x16 { return [x; 16]; }
fn vector_load_u16x16(xs: const u16[:], first: i64) -> u16x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: u16x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u16x16(xs: u16[:], first: i64, v: u16x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_u16x32(x: u16) -> u16x32 { return [x; 32]; }
fn vector_load_u16x32(xs: const u16[:], first: i64) -> u16x32 {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    var r: u16x32 = [0; 32];
    for i in 32 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u16x32(xs: u16[:], first: i64, v: u16x32) {
    assert(first >= 0 && xs.len >= 32 && first <= xs.len - 32);
    for i in 32 { xs[first + i] = v[i]; }
}
fn splat_i32x4(x: i32) -> i32x4 { return [x; 4]; }
fn vector_load_i32x4(xs: const i32[:], first: i64) -> i32x4 {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    var r: i32x4 = [0; 4];
    for i in 4 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i32x4(xs: i32[:], first: i64, v: i32x4) {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    for i in 4 { xs[first + i] = v[i]; }
}
fn splat_i32x8(x: i32) -> i32x8 { return [x; 8]; }
fn vector_load_i32x8(xs: const i32[:], first: i64) -> i32x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: i32x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i32x8(xs: i32[:], first: i64, v: i32x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_i32x16(x: i32) -> i32x16 { return [x; 16]; }
fn vector_load_i32x16(xs: const i32[:], first: i64) -> i32x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: i32x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i32x16(xs: i32[:], first: i64, v: i32x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_u32x4(x: u32) -> u32x4 { return [x; 4]; }
fn vector_load_u32x4(xs: const u32[:], first: i64) -> u32x4 {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    var r: u32x4 = [0; 4];
    for i in 4 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u32x4(xs: u32[:], first: i64, v: u32x4) {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    for i in 4 { xs[first + i] = v[i]; }
}
fn splat_u32x8(x: u32) -> u32x8 { return [x; 8]; }
fn vector_load_u32x8(xs: const u32[:], first: i64) -> u32x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: u32x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u32x8(xs: u32[:], first: i64, v: u32x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_u32x16(x: u32) -> u32x16 { return [x; 16]; }
fn vector_load_u32x16(xs: const u32[:], first: i64) -> u32x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: u32x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u32x16(xs: u32[:], first: i64, v: u32x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_i64x2(x: i64) -> i64x2 { return [x; 2]; }
fn vector_load_i64x2(xs: const i64[:], first: i64) -> i64x2 {
    assert(first >= 0 && xs.len >= 2 && first <= xs.len - 2);
    var r: i64x2 = [0; 2];
    for i in 2 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i64x2(xs: i64[:], first: i64, v: i64x2) {
    assert(first >= 0 && xs.len >= 2 && first <= xs.len - 2);
    for i in 2 { xs[first + i] = v[i]; }
}
fn splat_i64x4(x: i64) -> i64x4 { return [x; 4]; }
fn vector_load_i64x4(xs: const i64[:], first: i64) -> i64x4 {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    var r: i64x4 = [0; 4];
    for i in 4 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i64x4(xs: i64[:], first: i64, v: i64x4) {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    for i in 4 { xs[first + i] = v[i]; }
}
fn splat_i64x8(x: i64) -> i64x8 { return [x; 8]; }
fn vector_load_i64x8(xs: const i64[:], first: i64) -> i64x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: i64x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_i64x8(xs: i64[:], first: i64, v: i64x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_u64x2(x: u64) -> u64x2 { return [x; 2]; }
fn vector_load_u64x2(xs: const u64[:], first: i64) -> u64x2 {
    assert(first >= 0 && xs.len >= 2 && first <= xs.len - 2);
    var r: u64x2 = [0; 2];
    for i in 2 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u64x2(xs: u64[:], first: i64, v: u64x2) {
    assert(first >= 0 && xs.len >= 2 && first <= xs.len - 2);
    for i in 2 { xs[first + i] = v[i]; }
}
fn splat_u64x4(x: u64) -> u64x4 { return [x; 4]; }
fn vector_load_u64x4(xs: const u64[:], first: i64) -> u64x4 {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    var r: u64x4 = [0; 4];
    for i in 4 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u64x4(xs: u64[:], first: i64, v: u64x4) {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    for i in 4 { xs[first + i] = v[i]; }
}
fn splat_u64x8(x: u64) -> u64x8 { return [x; 8]; }
fn vector_load_u64x8(xs: const u64[:], first: i64) -> u64x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: u64x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_u64x8(xs: u64[:], first: i64, v: u64x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_f32x4(x: f32) -> f32x4 { return [x; 4]; }
fn vector_load_f32x4(xs: const f32[:], first: i64) -> f32x4 {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    var r: f32x4 = [0; 4];
    for i in 4 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_f32x4(xs: f32[:], first: i64, v: f32x4) {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    for i in 4 { xs[first + i] = v[i]; }
}
fn splat_f32x8(x: f32) -> f32x8 { return [x; 8]; }
fn vector_load_f32x8(xs: const f32[:], first: i64) -> f32x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: f32x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_f32x8(xs: f32[:], first: i64, v: f32x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}
fn splat_f32x16(x: f32) -> f32x16 { return [x; 16]; }
fn vector_load_f32x16(xs: const f32[:], first: i64) -> f32x16 {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    var r: f32x16 = [0; 16];
    for i in 16 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_f32x16(xs: f32[:], first: i64, v: f32x16) {
    assert(first >= 0 && xs.len >= 16 && first <= xs.len - 16);
    for i in 16 { xs[first + i] = v[i]; }
}
fn splat_f64x2(x: f64) -> f64x2 { return [x; 2]; }
fn vector_load_f64x2(xs: const f64[:], first: i64) -> f64x2 {
    assert(first >= 0 && xs.len >= 2 && first <= xs.len - 2);
    var r: f64x2 = [0; 2];
    for i in 2 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_f64x2(xs: f64[:], first: i64, v: f64x2) {
    assert(first >= 0 && xs.len >= 2 && first <= xs.len - 2);
    for i in 2 { xs[first + i] = v[i]; }
}
fn splat_f64x4(x: f64) -> f64x4 { return [x; 4]; }
fn vector_load_f64x4(xs: const f64[:], first: i64) -> f64x4 {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    var r: f64x4 = [0; 4];
    for i in 4 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_f64x4(xs: f64[:], first: i64, v: f64x4) {
    assert(first >= 0 && xs.len >= 4 && first <= xs.len - 4);
    for i in 4 { xs[first + i] = v[i]; }
}
fn splat_f64x8(x: f64) -> f64x8 { return [x; 8]; }
fn vector_load_f64x8(xs: const f64[:], first: i64) -> f64x8 {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    var r: f64x8 = [0; 8];
    for i in 8 { r[i] = xs[first + i]; }
    return r;
}
fn vector_store_f64x8(xs: f64[:], first: i64, v: f64x8) {
    assert(first >= 0 && xs.len >= 8 && first <= xs.len - 8);
    for i in 8 { xs[first + i] = v[i]; }
}

// Lane permutations. Each source index is checked by ordinary fixed-array
// indexing before the result value is returned.
fn shuffle_i8x16(v: i8x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> i8x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_i8x32(v: i8x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> i8x32 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15], v[k16], v[k17], v[k18], v[k19], v[k20], v[k21], v[k22], v[k23], v[k24], v[k25], v[k26], v[k27], v[k28], v[k29], v[k30], v[k31]]; }
fn shuffle_i8x64(v: i8x64, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64, k32: i64, k33: i64, k34: i64, k35: i64, k36: i64, k37: i64, k38: i64, k39: i64, k40: i64, k41: i64, k42: i64, k43: i64, k44: i64, k45: i64, k46: i64, k47: i64, k48: i64, k49: i64, k50: i64, k51: i64, k52: i64, k53: i64, k54: i64, k55: i64, k56: i64, k57: i64, k58: i64, k59: i64, k60: i64, k61: i64, k62: i64, k63: i64) -> i8x64 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15], v[k16], v[k17], v[k18], v[k19], v[k20], v[k21], v[k22], v[k23], v[k24], v[k25], v[k26], v[k27], v[k28], v[k29], v[k30], v[k31], v[k32], v[k33], v[k34], v[k35], v[k36], v[k37], v[k38], v[k39], v[k40], v[k41], v[k42], v[k43], v[k44], v[k45], v[k46], v[k47], v[k48], v[k49], v[k50], v[k51], v[k52], v[k53], v[k54], v[k55], v[k56], v[k57], v[k58], v[k59], v[k60], v[k61], v[k62], v[k63]]; }
fn shuffle_u8x16(v: u8x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> u8x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_u8x32(v: u8x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> u8x32 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15], v[k16], v[k17], v[k18], v[k19], v[k20], v[k21], v[k22], v[k23], v[k24], v[k25], v[k26], v[k27], v[k28], v[k29], v[k30], v[k31]]; }
fn shuffle_u8x64(v: u8x64, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64, k32: i64, k33: i64, k34: i64, k35: i64, k36: i64, k37: i64, k38: i64, k39: i64, k40: i64, k41: i64, k42: i64, k43: i64, k44: i64, k45: i64, k46: i64, k47: i64, k48: i64, k49: i64, k50: i64, k51: i64, k52: i64, k53: i64, k54: i64, k55: i64, k56: i64, k57: i64, k58: i64, k59: i64, k60: i64, k61: i64, k62: i64, k63: i64) -> u8x64 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15], v[k16], v[k17], v[k18], v[k19], v[k20], v[k21], v[k22], v[k23], v[k24], v[k25], v[k26], v[k27], v[k28], v[k29], v[k30], v[k31], v[k32], v[k33], v[k34], v[k35], v[k36], v[k37], v[k38], v[k39], v[k40], v[k41], v[k42], v[k43], v[k44], v[k45], v[k46], v[k47], v[k48], v[k49], v[k50], v[k51], v[k52], v[k53], v[k54], v[k55], v[k56], v[k57], v[k58], v[k59], v[k60], v[k61], v[k62], v[k63]]; }
fn shuffle_i16x8(v: i16x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> i16x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_i16x16(v: i16x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> i16x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_i16x32(v: i16x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> i16x32 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15], v[k16], v[k17], v[k18], v[k19], v[k20], v[k21], v[k22], v[k23], v[k24], v[k25], v[k26], v[k27], v[k28], v[k29], v[k30], v[k31]]; }
fn shuffle_u16x8(v: u16x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> u16x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_u16x16(v: u16x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> u16x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_u16x32(v: u16x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> u16x32 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15], v[k16], v[k17], v[k18], v[k19], v[k20], v[k21], v[k22], v[k23], v[k24], v[k25], v[k26], v[k27], v[k28], v[k29], v[k30], v[k31]]; }
fn shuffle_i32x4(v: i32x4, k0: i64, k1: i64, k2: i64, k3: i64) -> i32x4 { return [v[k0], v[k1], v[k2], v[k3]]; }
fn shuffle_i32x8(v: i32x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> i32x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_i32x16(v: i32x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> i32x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_u32x4(v: u32x4, k0: i64, k1: i64, k2: i64, k3: i64) -> u32x4 { return [v[k0], v[k1], v[k2], v[k3]]; }
fn shuffle_u32x8(v: u32x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> u32x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_u32x16(v: u32x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> u32x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_i64x2(v: i64x2, k0: i64, k1: i64) -> i64x2 { return [v[k0], v[k1]]; }
fn shuffle_i64x4(v: i64x4, k0: i64, k1: i64, k2: i64, k3: i64) -> i64x4 { return [v[k0], v[k1], v[k2], v[k3]]; }
fn shuffle_i64x8(v: i64x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> i64x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_u64x2(v: u64x2, k0: i64, k1: i64) -> u64x2 { return [v[k0], v[k1]]; }
fn shuffle_u64x4(v: u64x4, k0: i64, k1: i64, k2: i64, k3: i64) -> u64x4 { return [v[k0], v[k1], v[k2], v[k3]]; }
fn shuffle_u64x8(v: u64x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> u64x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_f32x4(v: f32x4, k0: i64, k1: i64, k2: i64, k3: i64) -> f32x4 { return [v[k0], v[k1], v[k2], v[k3]]; }
fn shuffle_f32x8(v: f32x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> f32x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }
fn shuffle_f32x16(v: f32x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> f32x16 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7], v[k8], v[k9], v[k10], v[k11], v[k12], v[k13], v[k14], v[k15]]; }
fn shuffle_f64x2(v: f64x2, k0: i64, k1: i64) -> f64x2 { return [v[k0], v[k1]]; }
fn shuffle_f64x4(v: f64x4, k0: i64, k1: i64, k2: i64, k3: i64) -> f64x4 { return [v[k0], v[k1], v[k2], v[k3]]; }
fn shuffle_f64x8(v: f64x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> f64x8 { return [v[k0], v[k1], v[k2], v[k3], v[k4], v[k5], v[k6], v[k7]]; }

