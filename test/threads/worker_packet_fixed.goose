// runtime-debug: fixed scalar arguments can follow any byte-sized prefix.
struct Large { bytes: u8[33] }
var evaluated: u8 = 0;
fn next() -> u64 { evaluated += 1; 123456789 }
thread_fn worker(prefix: u8, n: u64, value: f64, large: Large) {
    assert(prefix == 7 && n == 123456789 && value == 1.25);
    assert(large.bytes[0] == 1 && large.bytes[32] == 33);
}
fn main() {
    var large = Large { bytes: [0; 33] };
    large.bytes[0] = 1; large.bytes[32] = 33;
    assert(thread_wait(thread_spawn(worker, 7, next(), 1.25, large)));
    assert(evaluated == 1);
    assert(thread_wait(thread_spawn_contained(worker, 7, next(), 1.25, large)));
    assert(evaluated == 2 && large.bytes[32] == 33);
    print("worker packet fixed passed");
}
