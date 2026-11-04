import simd_vectors;

struct Wrapper<T> { value: T }

// error: explicit vectors have no public C ABI
extern fn take(value: const Wrapper<u32x4>&);

fn main() {}
