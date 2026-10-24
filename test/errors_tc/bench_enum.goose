// error: bench results must be fixed-width integers, bool, f32 or f64
enum E { A }
bench "bad" fn bad() -> E { abort("never"); }
fn main() {}
