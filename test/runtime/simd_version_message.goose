// A SIMD loop marker must not rewrite user text or its recorded byte length.
simd fn fail(n: i64) {
    var values: i64[>..] = [];
    print(values.check_length(n, "version@"));
}

fn main() { fail(-1); }
