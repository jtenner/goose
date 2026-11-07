var global: i16[u8] = [-3, 7];
fn add(a: i64[]&, n: i64) { a[0] += n; }
fn same(a: i64[]&, b: i64[]&) -> bool { a == b }
fn echo(a: const i64[]&) -> const i64[]& { a }
fn allocate(n: i64) -> i64 { var local: i64[] = [n, n + 1]; local[0] + local[1] }
fn main() {
    print("before=", allocate(5));
    var a: i64[] = [1, 2, 3]; var b: i64[] = [1, 2, 3];
    let stable = &a[0];
    var short: u8[u8] = [255, 0, 17]; var medium: i16[u16] = [-32768, 2];
    var wide: u32[u64] = [4294967295, 0]; var floating: f32[u8] = [-0.0, 2.5];
    var flags: bool[] = [true, false];
    var refs: i64&[u8] = [a[0], b[1]];
    refs[0] += 4; for &v in refs { v += 2; } add(a, 3);
    for &v, i in a { v += i; }
    print(a.len, ",", a[0], ",", a[1], ",", a[2], ",", stable);
    assert(stable .== &a[0]); print(echo(a)[1]);
    var matching: i64[] = [10, 3, 5]; print(same(a, matching), ",", a == b);
    print(short.len, ",", short[0], ",", medium[0], ",", wide[0]);
    print(floating[0], ",", floating[1], ",", flags[0], ",", flags[1]);
    var current: i64[]& = a;
    for v, i in current { print("walk=", v); if i == 0 { current .= b; } }
    global[1] += 1; print(global.len, ",", global[0], ",", global[1]);
    var empty: i64[u64] = []; print("empty=", empty.len);
    print("after=", allocate(7));
}
