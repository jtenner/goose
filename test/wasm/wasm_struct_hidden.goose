struct Hidden { data: i64[]? }
var depth: i64 = 1;
recursive fn bounce(x: Hidden?, n: i64) -> Hidden? {
    if n > 0 { return bounce(x, n - 1); }
    return x;
}
fn main() { var p: Hidden? = null; print(bounce(p, depth) == null); }
