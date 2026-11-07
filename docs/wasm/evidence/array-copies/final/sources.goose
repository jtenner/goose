var calls: i64 = 0;
var seed: i64[] = [7, 8];
var duplicate: i64[] = copy(seed);
fn choose(a: i64[]&) -> i64[]& {
    calls += 1;
    var scratch: u8[] = [11, 12];
    a[0] += scratch[0];
    return a;
}
fn main() {
    var a: i64[] = [1, 2];
    var b: i64[] = copy(choose(a));
    assert(calls == 1); b[0] += 100;
    print("once=", calls, ",", a[0], ",", b[0]);
    var refs: i64[]&[1] = [a];
    var c: i64[] = copy(refs[0]); c[1] = 30;
    print("index=", a[1], ",", c[1]);
    var optional: i64[]? = null; optional .= a;
    if optional != null {
        var d: i64[] = copy(optional); d[0] = 40;
        print("optional=", a[0], ",", d[0]);
    }
    duplicate[0] = 50;
    print("globals=", seed[0], ",", duplicate[0], ",", duplicate.len);
}
