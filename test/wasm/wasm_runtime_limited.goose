var global: i64[..] = [7, 8];
var calls = 0;
fn capacity(n: i64) -> i64 { calls++; var scratch: i64[] = [n]; return scratch[0]; }
recursive fn allocate(n: i64) -> i64 {
    var a: i64[..] = [..capacity(n)];
    for i in n { a.push(i + 1); }
    let last = a.pop(); a.push(last + 10);
    return a.cap + a.len + a[n - 1];
}
fn append(a: i64[..]&, n: i64) { a.push(n); }
fn echo(a: const i64[..]&) -> const i64[..]& { return a; }
fn main() {
    print("before=", allocate(3));
    var a: i64[..] = [..capacity(5)];
    print("initial=", a.cap, ",", a.len);
    append(a, 10); a.push(20);
    { let stable = &a[0]; a.push(30); a.push(40);
      print("alias=", stable, ",", a.len, ",", echo(a)[3]); }
    for &v, i in a { v += i; }
    print("values=", a[0], ",", a[3]);
    print("pop=", a.pop()); a.push(99); print("regrow=", a[3]);
    var b: i64[..] = [10, 21, 32, 99]; print("equal=", a == b, ",", b.cap);
    var zero: i64[..] = [..0]; print("zero=", zero.cap, ",", zero.len);
    var filled: i16[..] = [-2; 3]; print("fill=", filled.cap, ",", filled.len, ",", filled[2]);
    var refvalue: i64 = 4; var refs: i64&[..] = [..2]; refs.push(refvalue); refs.push(refvalue);
    for &v in refs { v += 2; } print("refs=", refvalue, ",", refs[0]);
    var floats: f32[..] = [..2]; floats.push(-0.0); floats.push(2.5);
    var flags: bool[..] = [true, false];
    print("scalar=", floats[0], ",", floats[1], ",", flags[1]);
    b[1] = 200;
    var owners: i64[..]&[2] = [a, b];
    for v, i in owners[0] { print("path=", v); if i == 0 { owners[0] .= b; } }
    print("global=", global.cap, ",", global.len, ",", global[1]);
    var total: i64 = 0;
    for i in 10000 { var temp: i64[..] = [..3]; temp.push(i); total += temp[0]; }
    print("reuse=", total);
    print("after=", allocate(4), ",", calls);
}
