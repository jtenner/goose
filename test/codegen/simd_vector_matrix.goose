// Explicit vector width/type matrix. Every standard shape typechecks and runs on scalar backends;
// native generated-C shape checks cover arithmetic separately.
import simd_vectors;
import std;
fn main() {
    let a_i8x16 = splat_i8x16(2); let b_i8x16 = splat_i8x16(3); print((a_i8x16 + b_i8x16)[0], " ");
    let a_i8x32 = splat_i8x32(2); let b_i8x32 = splat_i8x32(3); print((a_i8x32 + b_i8x32)[0], " ");
    let a_i8x64 = splat_i8x64(2); let b_i8x64 = splat_i8x64(3); print((a_i8x64 + b_i8x64)[0], " ");
    let a_u8x16 = splat_u8x16(2); let b_u8x16 = splat_u8x16(3); print((a_u8x16 + b_u8x16)[0], " ");
    let a_u8x32 = splat_u8x32(2); let b_u8x32 = splat_u8x32(3); print((a_u8x32 + b_u8x32)[0], " ");
    let a_u8x64 = splat_u8x64(2); let b_u8x64 = splat_u8x64(3); print((a_u8x64 + b_u8x64)[0], " ");
    let a_i16x8 = splat_i16x8(2); let b_i16x8 = splat_i16x8(3); print((a_i16x8 + b_i16x8)[0], " ");
    let a_i16x16 = splat_i16x16(2); let b_i16x16 = splat_i16x16(3); print((a_i16x16 + b_i16x16)[0], " ");
    let a_i16x32 = splat_i16x32(2); let b_i16x32 = splat_i16x32(3); print((a_i16x32 + b_i16x32)[0], " ");
    let a_u16x8 = splat_u16x8(2); let b_u16x8 = splat_u16x8(3); print((a_u16x8 + b_u16x8)[0], " ");
    let a_u16x16 = splat_u16x16(2); let b_u16x16 = splat_u16x16(3); print((a_u16x16 + b_u16x16)[0], " ");
    let a_u16x32 = splat_u16x32(2); let b_u16x32 = splat_u16x32(3); print((a_u16x32 + b_u16x32)[0], " ");
    let a_i32x4 = splat_i32x4(2); let b_i32x4 = splat_i32x4(3); print((a_i32x4 + b_i32x4)[0], " ");
    let a_i32x8 = splat_i32x8(2); let b_i32x8 = splat_i32x8(3); print((a_i32x8 + b_i32x8)[0], " ");
    let a_i32x16 = splat_i32x16(2); let b_i32x16 = splat_i32x16(3); print((a_i32x16 + b_i32x16)[0], " ");
    let a_u32x4 = splat_u32x4(2); let b_u32x4 = splat_u32x4(3); print((a_u32x4 + b_u32x4)[0], " ");
    let a_u32x8 = splat_u32x8(2); let b_u32x8 = splat_u32x8(3); print((a_u32x8 + b_u32x8)[0], " ");
    let a_u32x16 = splat_u32x16(2); let b_u32x16 = splat_u32x16(3); print((a_u32x16 + b_u32x16)[0], " ");
    let a_i64x2 = splat_i64x2(2); let b_i64x2 = splat_i64x2(3); print((a_i64x2 + b_i64x2)[0], " ");
    let a_i64x4 = splat_i64x4(2); let b_i64x4 = splat_i64x4(3); print((a_i64x4 + b_i64x4)[0], " ");
    let a_i64x8 = splat_i64x8(2); let b_i64x8 = splat_i64x8(3); print((a_i64x8 + b_i64x8)[0], " ");
    let a_u64x2 = splat_u64x2(2); let b_u64x2 = splat_u64x2(3); print((a_u64x2 + b_u64x2)[0], " ");
    let a_u64x4 = splat_u64x4(2); let b_u64x4 = splat_u64x4(3); print((a_u64x4 + b_u64x4)[0], " ");
    let a_u64x8 = splat_u64x8(2); let b_u64x8 = splat_u64x8(3); print((a_u64x8 + b_u64x8)[0], " ");
    let a_f32x4 = splat_f32x4(2); let b_f32x4 = splat_f32x4(3); print((a_f32x4 + b_f32x4)[0], " ");
    let a_f32x8 = splat_f32x8(2); let b_f32x8 = splat_f32x8(3); print((a_f32x8 + b_f32x8)[0], " ");
    let a_f32x16 = splat_f32x16(2); let b_f32x16 = splat_f32x16(3); print((a_f32x16 + b_f32x16)[0], " ");
    let a_f64x2 = splat_f64x2(2); let b_f64x2 = splat_f64x2(3); print((a_f64x2 + b_f64x2)[0], " ");
    let a_f64x4 = splat_f64x4(2); let b_f64x4 = splat_f64x4(3); print((a_f64x4 + b_f64x4)[0], " ");
    let a_f64x8 = splat_f64x8(2); let b_f64x8 = splat_f64x8(3); print((a_f64x8 + b_f64x8)[0], " ");
    print("done");
}
