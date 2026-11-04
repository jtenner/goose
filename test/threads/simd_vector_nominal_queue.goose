// no-jit: queues require the native threads runtime.
import simd_vectors;

fn main() {
    qput(splat_u32x4(7));
    let ignored, array_ok = qpoll<u32[4]>();
    let vector, vector_ok = qpoll<u32x4>();
    assert(!array_ok && vector_ok && vector[0] == 7);
    print("nominal vector queue ok");
}
