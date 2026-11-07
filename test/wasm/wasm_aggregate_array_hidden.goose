struct Hidden { n: i64, bytes: u8[]? }
recursive fn bounce(p: Hidden&, n: i64) -> Hidden& { if n > 0 { return bounce(p, n - 1); } return p; }
recursive fn through(a: Hidden[2]&) -> Hidden& { bounce(a[1], 1) }
fn main() { var a: Hidden[2] = [Hidden { n: 7 }, Hidden { n: 8 }]; var p: Hidden& = through(a); assert(p.n == 8); print("hidden=", p.n); }
