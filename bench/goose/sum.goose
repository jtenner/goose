// Control benchmark: a flat array of scalars, scanned repeatedly. Nothing here
// plays to a Goose strength -- the data is fixed-size, contiguous in every
// language, and the loop is the same machine code. A dead heat here is the
// evidence that the harness measures the algorithm and not the toolchain.

import rng;

// Keep in sync with run_bench.py: small / medium / large.
let N = if build::BENCH_SIZE == "small" { 1000000 }
        else if build::BENCH_SIZE == "medium" { 16000000 } else { 128000000 };
let PASSES = 8;

bench "Build and scan a scalar array" fn sum_generated() -> i64, i64 {
    var data: i32[>..] = [];
    var r: u64 = 12345;
    for i in N {
        r = xs_next(r);
        data.push(xs_mod(r, 1000) as i32);
    }
    var total = 0;
    for p in PASSES {
        // The `^ p` keeps the passes from collapsing into one multiply.
        for x in data { total += x ^ p; }
    }
    return data.len, total;
}

// Compatibility entry for whole-process experiments. Supply BENCH_SIZE.
fn main() {
    let count, total = sum_generated();
    print(count);
    print(total);
}
