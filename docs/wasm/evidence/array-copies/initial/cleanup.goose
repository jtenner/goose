recursive fn probe(a: i64[]&, early: bool) -> i64 {
    var b: i64[] = copy(a);
    defer { var c: i64[] = copy(b); print("defer=", c[0]); }
    if early { return b[0]; }
    b[0] += 1; return b[0];
}
fn main() {
    var a: i64[] = [10];
    print("early=", probe(a, true));
    { var live: i64[] = [99]; print("normal=", probe(a, false)); print(live[0]); }
    for i in 3 {
        var b: i64[] = copy(a);
        defer { var c: i64[] = copy(b); print("loop=", i, ",", c[0]); }
        if i == 0 { continue; } if i == 1 { break; }
    }
    print("source=", a[0]);
}
