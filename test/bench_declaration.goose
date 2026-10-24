// dump-runtime
/// A benchmark with escaped metadata.
bench /* contextual prefix */ "Line\n\"quoted\"\t\\" fn measured::pair() -> i64, bool { return 42, true; }
bench "same" fn inferred() { 7 }
bench "same" fn floats() -> f32, f64 { return 1.0, 2.0; }
bench "widths" fn widths() -> i8, u8, i16, u16, i32, u32, i64, u64 {
    return -1, 1, -2, 2, -3, 3, -4, 18446744073709551615;
}
bench "inferred pair" fn inferred_pair() { return 1, false; }
bench "qualified main" fn ns::main() { 1 }
fn main() {
    let bench = inferred();
    let n, ok = measured::pair();
    print(bench, " ", n, " ", ok);
}
