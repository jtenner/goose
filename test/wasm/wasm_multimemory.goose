var global: i64[>..] = [];
fn push_one(a: i64[>..]&, n: i64) { a.push(n); }
fn get(a: const i64[>..]&, i: i64) -> i64 { a[i] }
recursive fn scratch(n: i64) -> i64 {
    if n > 0 { return scratch(n - 1); }
    var a: i64[>..] = [7];
    return a[0];
}
fn main() {
    print("before=", scratch(3));
    var a: i64[>..] = [3, 5];
    var b: i64[>..] = [7];
    push_one(a, 11);
    let keep = &a[0];
    for i in 10000 { a.push(i); b.push(-i); }
    print(a.len, ",", b.len, ",", keep, ",", b[0], ",", a[10001]);
    keep += 2;
    print(a[0], ",", get(b, 1));
    assert(keep .!= &b[0]);
    var refs: i64&[>..] = [];
    refs.push(keep);
    refs.push(b[0]);
    refs[0] += 4;
    print(a[0], ",", refs[0]);
    refs[0] .= b[0];
    refs[0] += 10;
    print(a[0], ",", b[0], ",", refs[0]);
    var optional: i64? = null;
    print(optional == null);
    optional .= keep;
    if optional && optional != null { optional += 1; }
    print(optional, ",", optional .== keep);
    for &value, i in a {
        if i >= 3 { break; }
        value += 1;
    }
    print(a[0], ",", a[1], ",", a[2]);
    var c: i64[>..] = [0];
    for &value, i in c { if i < 3 { c.push(i + 1); } value += 1; }
    print(c.len, ",", c[3]);
    global.push(17); global.push(19);
    print(global.len, ",", global[1]);
    {
        var temporary: i64[>..] = [9];
        defer print("defer=", temporary[0]);
    }
    print("after=", scratch(3));
}
