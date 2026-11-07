var global: i64[] = [7, 8];
recursive fn copied(a: i64[]&) -> i64 {
    var b: i64[] = copy(a); b[0] += 100;
    return b.len + b[0];
}
recursive fn copied_cap(a: i64[..]&) -> i64 {
    var b: i64[..] = copy(a); b.push(9); return b.cap + b.len;
}
fn echo(a: const i64[]&) -> const i64[]& { return a; }
fn main() {
    print("before=", copied(global));
    var a: i64[] = [1, 2, 3]; var b: i64[] = copy(a); b[0] = 90;
    print("variable=", a[0], ",", b[0], ",", b.len);
    assert(&a[0] .!= &b[0]);
    var fixed: i64[3] = [4, 5, 6]; var fixedcopy: i64[3] = fixed;
    fixedcopy[1] = 20; print("fixed=", fixed[1], ",", fixedcopy[1]);
    var limited: i64[..4] = [10, 11]; var limitedcopy: i64[..4] = copy(limited);
    limitedcopy.push(12); print("limited=", limited.len, ",", limitedcopy.len, ",", limitedcopy[2]);
    var runtime: i64[..] = [..5]; runtime.push(30); runtime.push(31);
    var runtimecopy: i64[..] = copy(runtime); runtimecopy.push(32);
    print("runtime=", runtime.len, ",", runtimecopy.cap, ",", runtimecopy.len, ",", copied_cap(runtime));
    var grow: i64[>..] = [40, 41]; var growcopy: i64[>..] = copy(grow);
    growcopy.push(42); print("grow=", grow.len, ",", growcopy.len, ",", growcopy[2]);
    var shrink: f64[>..<] = [-0.0, 1.5]; var shrinkcopy: f64[>..<] = copy(shrink);
    shrinkcopy.pop(); print("shrink=", shrink.len, ",", shrinkcopy.len, ",", shrinkcopy[0]);
    var scalar: i64 = 50; var refs: i64&[] = [scalar]; var refcopy: i64&[] = copy(refs);
    refcopy[0] += 3; assert(refs[0] .== refcopy[0]); print("refs=", scalar, ",", refs[0]);
    var borrowed: i64[] = copy(echo(a)); borrowed[2] = 70;
    print("borrowed=", a[2], ",", borrowed[2]);
    var empty: i64[u64] = []; var emptycopy: i64[u64] = copy(empty); print("empty=", emptycopy.len);
    var payload: u8[>..] = []; for i in 70000 { payload.push(120); }
    var payloadcopy: u8[>..] = copy(payload); payloadcopy[0] = 121;
    print("large=", payload.len, ",", payload[0], ",", payloadcopy.len, ",", payloadcopy[0], ",", payloadcopy[69999]);
    print("after=", copied(a), ",", a[0], ",", global[0]);
}
