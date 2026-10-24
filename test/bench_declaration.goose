// dump-runtime
/// A benchmark with escaped metadata.
bench /* contextual prefix */ "Line\n\"quoted\"\t\\" fn measured::pair() -> i64, bool { return 42, true; }
bench "same" fn inferred() { 7 }
bench "same" fn floats() -> f32, f64 { return 1.0, 2.0; }
fn main() {
    let bench = inferred();
    let n, ok = measured::pair();
    print(bench, " ", n, " ", ok);
}
