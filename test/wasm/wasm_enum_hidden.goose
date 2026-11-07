enum Hidden { None, More { next: Hidden?, bytes: u8[]? } }
recursive fn bounce(p: Hidden?, n: i64) -> Hidden? { if n > 0 { return bounce(p, n - 1); } return p; }
enum Mixed { Fixed { n: i64 }, Variable { bytes: u8[] } }
fn main() { var p: Hidden? = null; assert(bounce(p, 1) == null); var v: Mixed.Fixed = Mixed.Fixed { n: 17 }; assert(v.n == 17); print("hidden"); }
