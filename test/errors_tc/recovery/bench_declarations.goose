// error: bench requires an unmodified fn declaration
// error: bench label must be nonempty
// error: type expected, found ')'
bench "bad modifier" recursive fn first() { 1 }
bench "" fn second() { 2 }
bench "malformed signature" fn third(value:) -> i64 { 3 }
bench "valid after recovery" fn fourth() { 4 }
fn main() {}
