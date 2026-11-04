// Explicit fixed-width SIMD values (spec §7.12). Each alias names a nominal
// vector type with packed, byte-aligned, flat storage that remains available
// to scalar-only backends. The C backend recognizes the same shapes for its
// GS_VEC expression lowering.

type i8x16 = vector i8[16];
type i8x32 = vector i8[32];
type i8x64 = vector i8[64];
type u8x16 = vector u8[16];
type u8x32 = vector u8[32];
type u8x64 = vector u8[64];
type i16x8 = vector i16[8];
type i16x16 = vector i16[16];
type i16x32 = vector i16[32];
type u16x8 = vector u16[8];
type u16x16 = vector u16[16];
type u16x32 = vector u16[32];
type i32x4 = vector i32[4];
type i32x8 = vector i32[8];
type i32x16 = vector i32[16];
type u32x4 = vector u32[4];
type u32x8 = vector u32[8];
type u32x16 = vector u32[16];
type i64x2 = vector i64[2];
type i64x4 = vector i64[4];
type i64x8 = vector i64[8];
type u64x2 = vector u64[2];
type u64x4 = vector u64[4];
type u64x8 = vector u64[8];
type f32x4 = vector f32[4];
type f32x8 = vector f32[8];
type f32x16 = vector f32[16];
type f64x2 = vector f64[2];
type f64x4 = vector f64[4];
type f64x8 = vector f64[8];

fn splat_i8x16(x: i8) -> i8x16 { return __simd_splat<i8x16>(x); }
fn vector_load_i8x16(xs: const i8[:], first: i64) -> i8x16 {
    return __simd_load<i8x16>(xs, first);
}
fn vector_store_i8x16(xs: i8[:], first: i64, v: i8x16) {
    __simd_store<i8x16>(xs, first, v);
}
fn splat_i8x32(x: i8) -> i8x32 { return __simd_splat<i8x32>(x); }
fn vector_load_i8x32(xs: const i8[:], first: i64) -> i8x32 {
    return __simd_load<i8x32>(xs, first);
}
fn vector_store_i8x32(xs: i8[:], first: i64, v: i8x32) {
    __simd_store<i8x32>(xs, first, v);
}
fn splat_i8x64(x: i8) -> i8x64 { return __simd_splat<i8x64>(x); }
fn vector_load_i8x64(xs: const i8[:], first: i64) -> i8x64 {
    return __simd_load<i8x64>(xs, first);
}
fn vector_store_i8x64(xs: i8[:], first: i64, v: i8x64) {
    __simd_store<i8x64>(xs, first, v);
}
fn splat_u8x16(x: u8) -> u8x16 { return __simd_splat<u8x16>(x); }
fn vector_load_u8x16(xs: const u8[:], first: i64) -> u8x16 {
    return __simd_load<u8x16>(xs, first);
}
fn vector_store_u8x16(xs: u8[:], first: i64, v: u8x16) {
    __simd_store<u8x16>(xs, first, v);
}
fn splat_u8x32(x: u8) -> u8x32 { return __simd_splat<u8x32>(x); }
fn vector_load_u8x32(xs: const u8[:], first: i64) -> u8x32 {
    return __simd_load<u8x32>(xs, first);
}
fn vector_store_u8x32(xs: u8[:], first: i64, v: u8x32) {
    __simd_store<u8x32>(xs, first, v);
}
fn splat_u8x64(x: u8) -> u8x64 { return __simd_splat<u8x64>(x); }
fn vector_load_u8x64(xs: const u8[:], first: i64) -> u8x64 {
    return __simd_load<u8x64>(xs, first);
}
fn vector_store_u8x64(xs: u8[:], first: i64, v: u8x64) {
    __simd_store<u8x64>(xs, first, v);
}
fn splat_i16x8(x: i16) -> i16x8 { return __simd_splat<i16x8>(x); }
fn vector_load_i16x8(xs: const i16[:], first: i64) -> i16x8 {
    return __simd_load<i16x8>(xs, first);
}
fn vector_store_i16x8(xs: i16[:], first: i64, v: i16x8) {
    __simd_store<i16x8>(xs, first, v);
}
fn splat_i16x16(x: i16) -> i16x16 { return __simd_splat<i16x16>(x); }
fn vector_load_i16x16(xs: const i16[:], first: i64) -> i16x16 {
    return __simd_load<i16x16>(xs, first);
}
fn vector_store_i16x16(xs: i16[:], first: i64, v: i16x16) {
    __simd_store<i16x16>(xs, first, v);
}
fn splat_i16x32(x: i16) -> i16x32 { return __simd_splat<i16x32>(x); }
fn vector_load_i16x32(xs: const i16[:], first: i64) -> i16x32 {
    return __simd_load<i16x32>(xs, first);
}
fn vector_store_i16x32(xs: i16[:], first: i64, v: i16x32) {
    __simd_store<i16x32>(xs, first, v);
}
fn splat_u16x8(x: u16) -> u16x8 { return __simd_splat<u16x8>(x); }
fn vector_load_u16x8(xs: const u16[:], first: i64) -> u16x8 {
    return __simd_load<u16x8>(xs, first);
}
fn vector_store_u16x8(xs: u16[:], first: i64, v: u16x8) {
    __simd_store<u16x8>(xs, first, v);
}
fn splat_u16x16(x: u16) -> u16x16 { return __simd_splat<u16x16>(x); }
fn vector_load_u16x16(xs: const u16[:], first: i64) -> u16x16 {
    return __simd_load<u16x16>(xs, first);
}
fn vector_store_u16x16(xs: u16[:], first: i64, v: u16x16) {
    __simd_store<u16x16>(xs, first, v);
}
fn splat_u16x32(x: u16) -> u16x32 { return __simd_splat<u16x32>(x); }
fn vector_load_u16x32(xs: const u16[:], first: i64) -> u16x32 {
    return __simd_load<u16x32>(xs, first);
}
fn vector_store_u16x32(xs: u16[:], first: i64, v: u16x32) {
    __simd_store<u16x32>(xs, first, v);
}
fn splat_i32x4(x: i32) -> i32x4 { return __simd_splat<i32x4>(x); }
fn vector_load_i32x4(xs: const i32[:], first: i64) -> i32x4 {
    return __simd_load<i32x4>(xs, first);
}
fn vector_store_i32x4(xs: i32[:], first: i64, v: i32x4) {
    __simd_store<i32x4>(xs, first, v);
}
fn splat_i32x8(x: i32) -> i32x8 { return __simd_splat<i32x8>(x); }
fn vector_load_i32x8(xs: const i32[:], first: i64) -> i32x8 {
    return __simd_load<i32x8>(xs, first);
}
fn vector_store_i32x8(xs: i32[:], first: i64, v: i32x8) {
    __simd_store<i32x8>(xs, first, v);
}
fn splat_i32x16(x: i32) -> i32x16 { return __simd_splat<i32x16>(x); }
fn vector_load_i32x16(xs: const i32[:], first: i64) -> i32x16 {
    return __simd_load<i32x16>(xs, first);
}
fn vector_store_i32x16(xs: i32[:], first: i64, v: i32x16) {
    __simd_store<i32x16>(xs, first, v);
}
fn splat_u32x4(x: u32) -> u32x4 { return __simd_splat<u32x4>(x); }
fn vector_load_u32x4(xs: const u32[:], first: i64) -> u32x4 {
    return __simd_load<u32x4>(xs, first);
}
fn vector_store_u32x4(xs: u32[:], first: i64, v: u32x4) {
    __simd_store<u32x4>(xs, first, v);
}
fn splat_u32x8(x: u32) -> u32x8 { return __simd_splat<u32x8>(x); }
fn vector_load_u32x8(xs: const u32[:], first: i64) -> u32x8 {
    return __simd_load<u32x8>(xs, first);
}
fn vector_store_u32x8(xs: u32[:], first: i64, v: u32x8) {
    __simd_store<u32x8>(xs, first, v);
}
fn splat_u32x16(x: u32) -> u32x16 { return __simd_splat<u32x16>(x); }
fn vector_load_u32x16(xs: const u32[:], first: i64) -> u32x16 {
    return __simd_load<u32x16>(xs, first);
}
fn vector_store_u32x16(xs: u32[:], first: i64, v: u32x16) {
    __simd_store<u32x16>(xs, first, v);
}
fn splat_i64x2(x: i64) -> i64x2 { return __simd_splat<i64x2>(x); }
fn vector_load_i64x2(xs: const i64[:], first: i64) -> i64x2 {
    return __simd_load<i64x2>(xs, first);
}
fn vector_store_i64x2(xs: i64[:], first: i64, v: i64x2) {
    __simd_store<i64x2>(xs, first, v);
}
fn splat_i64x4(x: i64) -> i64x4 { return __simd_splat<i64x4>(x); }
fn vector_load_i64x4(xs: const i64[:], first: i64) -> i64x4 {
    return __simd_load<i64x4>(xs, first);
}
fn vector_store_i64x4(xs: i64[:], first: i64, v: i64x4) {
    __simd_store<i64x4>(xs, first, v);
}
fn splat_i64x8(x: i64) -> i64x8 { return __simd_splat<i64x8>(x); }
fn vector_load_i64x8(xs: const i64[:], first: i64) -> i64x8 {
    return __simd_load<i64x8>(xs, first);
}
fn vector_store_i64x8(xs: i64[:], first: i64, v: i64x8) {
    __simd_store<i64x8>(xs, first, v);
}
fn splat_u64x2(x: u64) -> u64x2 { return __simd_splat<u64x2>(x); }
fn vector_load_u64x2(xs: const u64[:], first: i64) -> u64x2 {
    return __simd_load<u64x2>(xs, first);
}
fn vector_store_u64x2(xs: u64[:], first: i64, v: u64x2) {
    __simd_store<u64x2>(xs, first, v);
}
fn splat_u64x4(x: u64) -> u64x4 { return __simd_splat<u64x4>(x); }
fn vector_load_u64x4(xs: const u64[:], first: i64) -> u64x4 {
    return __simd_load<u64x4>(xs, first);
}
fn vector_store_u64x4(xs: u64[:], first: i64, v: u64x4) {
    __simd_store<u64x4>(xs, first, v);
}
fn splat_u64x8(x: u64) -> u64x8 { return __simd_splat<u64x8>(x); }
fn vector_load_u64x8(xs: const u64[:], first: i64) -> u64x8 {
    return __simd_load<u64x8>(xs, first);
}
fn vector_store_u64x8(xs: u64[:], first: i64, v: u64x8) {
    __simd_store<u64x8>(xs, first, v);
}
fn splat_f32x4(x: f32) -> f32x4 { return __simd_splat<f32x4>(x); }
fn vector_load_f32x4(xs: const f32[:], first: i64) -> f32x4 {
    return __simd_load<f32x4>(xs, first);
}
fn vector_store_f32x4(xs: f32[:], first: i64, v: f32x4) {
    __simd_store<f32x4>(xs, first, v);
}
fn splat_f32x8(x: f32) -> f32x8 { return __simd_splat<f32x8>(x); }
fn vector_load_f32x8(xs: const f32[:], first: i64) -> f32x8 {
    return __simd_load<f32x8>(xs, first);
}
fn vector_store_f32x8(xs: f32[:], first: i64, v: f32x8) {
    __simd_store<f32x8>(xs, first, v);
}
fn splat_f32x16(x: f32) -> f32x16 { return __simd_splat<f32x16>(x); }
fn vector_load_f32x16(xs: const f32[:], first: i64) -> f32x16 {
    return __simd_load<f32x16>(xs, first);
}
fn vector_store_f32x16(xs: f32[:], first: i64, v: f32x16) {
    __simd_store<f32x16>(xs, first, v);
}
fn splat_f64x2(x: f64) -> f64x2 { return __simd_splat<f64x2>(x); }
fn vector_load_f64x2(xs: const f64[:], first: i64) -> f64x2 {
    return __simd_load<f64x2>(xs, first);
}
fn vector_store_f64x2(xs: f64[:], first: i64, v: f64x2) {
    __simd_store<f64x2>(xs, first, v);
}
fn splat_f64x4(x: f64) -> f64x4 { return __simd_splat<f64x4>(x); }
fn vector_load_f64x4(xs: const f64[:], first: i64) -> f64x4 {
    return __simd_load<f64x4>(xs, first);
}
fn vector_store_f64x4(xs: f64[:], first: i64, v: f64x4) {
    __simd_store<f64x4>(xs, first, v);
}
fn splat_f64x8(x: f64) -> f64x8 { return __simd_splat<f64x8>(x); }
fn vector_load_f64x8(xs: const f64[:], first: i64) -> f64x8 {
    return __simd_load<f64x8>(xs, first);
}
fn vector_store_f64x8(xs: f64[:], first: i64, v: f64x8) {
    __simd_store<f64x8>(xs, first, v);
}

// Lane permutations. Each source index is checked by ordinary fixed-array
// indexing before the result value is returned.
fn shuffle_i8x16(v: i8x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> i8x16 { return __simd_shuffle<i8x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_i8x32(v: i8x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> i8x32 { return __simd_shuffle<i8x32>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23, k24, k25, k26, k27, k28, k29, k30, k31); }
fn shuffle_i8x64(v: i8x64, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64, k32: i64, k33: i64, k34: i64, k35: i64, k36: i64, k37: i64, k38: i64, k39: i64, k40: i64, k41: i64, k42: i64, k43: i64, k44: i64, k45: i64, k46: i64, k47: i64, k48: i64, k49: i64, k50: i64, k51: i64, k52: i64, k53: i64, k54: i64, k55: i64, k56: i64, k57: i64, k58: i64, k59: i64, k60: i64, k61: i64, k62: i64, k63: i64) -> i8x64 { return __simd_shuffle<i8x64>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23, k24, k25, k26, k27, k28, k29, k30, k31, k32, k33, k34, k35, k36, k37, k38, k39, k40, k41, k42, k43, k44, k45, k46, k47, k48, k49, k50, k51, k52, k53, k54, k55, k56, k57, k58, k59, k60, k61, k62, k63); }
fn shuffle_u8x16(v: u8x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> u8x16 { return __simd_shuffle<u8x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_u8x32(v: u8x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> u8x32 { return __simd_shuffle<u8x32>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23, k24, k25, k26, k27, k28, k29, k30, k31); }
fn shuffle_u8x64(v: u8x64, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64, k32: i64, k33: i64, k34: i64, k35: i64, k36: i64, k37: i64, k38: i64, k39: i64, k40: i64, k41: i64, k42: i64, k43: i64, k44: i64, k45: i64, k46: i64, k47: i64, k48: i64, k49: i64, k50: i64, k51: i64, k52: i64, k53: i64, k54: i64, k55: i64, k56: i64, k57: i64, k58: i64, k59: i64, k60: i64, k61: i64, k62: i64, k63: i64) -> u8x64 { return __simd_shuffle<u8x64>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23, k24, k25, k26, k27, k28, k29, k30, k31, k32, k33, k34, k35, k36, k37, k38, k39, k40, k41, k42, k43, k44, k45, k46, k47, k48, k49, k50, k51, k52, k53, k54, k55, k56, k57, k58, k59, k60, k61, k62, k63); }
fn shuffle_i16x8(v: i16x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> i16x8 { return __simd_shuffle<i16x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_i16x16(v: i16x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> i16x16 { return __simd_shuffle<i16x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_i16x32(v: i16x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> i16x32 { return __simd_shuffle<i16x32>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23, k24, k25, k26, k27, k28, k29, k30, k31); }
fn shuffle_u16x8(v: u16x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> u16x8 { return __simd_shuffle<u16x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_u16x16(v: u16x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> u16x16 { return __simd_shuffle<u16x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_u16x32(v: u16x32, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64, k16: i64, k17: i64, k18: i64, k19: i64, k20: i64, k21: i64, k22: i64, k23: i64, k24: i64, k25: i64, k26: i64, k27: i64, k28: i64, k29: i64, k30: i64, k31: i64) -> u16x32 { return __simd_shuffle<u16x32>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23, k24, k25, k26, k27, k28, k29, k30, k31); }
fn shuffle_i32x4(v: i32x4, k0: i64, k1: i64, k2: i64, k3: i64) -> i32x4 { return __simd_shuffle<i32x4>(v, k0, k1, k2, k3); }
fn shuffle_i32x8(v: i32x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> i32x8 { return __simd_shuffle<i32x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_i32x16(v: i32x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> i32x16 { return __simd_shuffle<i32x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_u32x4(v: u32x4, k0: i64, k1: i64, k2: i64, k3: i64) -> u32x4 { return __simd_shuffle<u32x4>(v, k0, k1, k2, k3); }
fn shuffle_u32x8(v: u32x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> u32x8 { return __simd_shuffle<u32x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_u32x16(v: u32x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> u32x16 { return __simd_shuffle<u32x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_i64x2(v: i64x2, k0: i64, k1: i64) -> i64x2 { return __simd_shuffle<i64x2>(v, k0, k1); }
fn shuffle_i64x4(v: i64x4, k0: i64, k1: i64, k2: i64, k3: i64) -> i64x4 { return __simd_shuffle<i64x4>(v, k0, k1, k2, k3); }
fn shuffle_i64x8(v: i64x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> i64x8 { return __simd_shuffle<i64x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_u64x2(v: u64x2, k0: i64, k1: i64) -> u64x2 { return __simd_shuffle<u64x2>(v, k0, k1); }
fn shuffle_u64x4(v: u64x4, k0: i64, k1: i64, k2: i64, k3: i64) -> u64x4 { return __simd_shuffle<u64x4>(v, k0, k1, k2, k3); }
fn shuffle_u64x8(v: u64x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> u64x8 { return __simd_shuffle<u64x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_f32x4(v: f32x4, k0: i64, k1: i64, k2: i64, k3: i64) -> f32x4 { return __simd_shuffle<f32x4>(v, k0, k1, k2, k3); }
fn shuffle_f32x8(v: f32x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> f32x8 { return __simd_shuffle<f32x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }
fn shuffle_f32x16(v: f32x16, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64, k8: i64, k9: i64, k10: i64, k11: i64, k12: i64, k13: i64, k14: i64, k15: i64) -> f32x16 { return __simd_shuffle<f32x16>(v, k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12, k13, k14, k15); }
fn shuffle_f64x2(v: f64x2, k0: i64, k1: i64) -> f64x2 { return __simd_shuffle<f64x2>(v, k0, k1); }
fn shuffle_f64x4(v: f64x4, k0: i64, k1: i64, k2: i64, k3: i64) -> f64x4 { return __simd_shuffle<f64x4>(v, k0, k1, k2, k3); }
fn shuffle_f64x8(v: f64x8, k0: i64, k1: i64, k2: i64, k3: i64, k4: i64, k5: i64, k6: i64, k7: i64) -> f64x8 { return __simd_shuffle<f64x8>(v, k0, k1, k2, k3, k4, k5, k6, k7); }

