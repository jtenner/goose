recursive fn probe(a: i64[varint]&, early: bool) -> i64 {
    var b: i64[varint] = copy(a);
    defer { var c: i64[varint] = copy(b); print("defer=", c.len, ",", c[0]); }
    if early { return b[0]; } b[0] += 1; return b[0];
}
fn main() {
    var a: i64[varint] = [7; 128];
    print(probe(a, true));
    { var live: u8[varint] = [3]; print(probe(a, false)); print(live[0]); }
    for i in 3 {
        var b: i64[varint] = copy(a);
        defer { var c: i64[varint] = copy(b); print("loop=", i, ",", c[127]); }
        if i == 0 { continue; } if i == 1 { break; }
    }
    print("source=", a[0]);
}
