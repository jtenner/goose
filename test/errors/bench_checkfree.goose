// error: bench requires an unmodified fn declaration
bench "x" checkfree fn bad() -> i64 { 1 }
