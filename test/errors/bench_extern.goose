// error: bench requires an unmodified fn declaration
bench "x" extern fn bad() -> i64 { 1 }
