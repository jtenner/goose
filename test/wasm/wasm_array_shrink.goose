fn clear_all(a: i64[>..<]&) { a.clear(); }
fn take_last(a: i64[>..<]&) -> i64 { a.pop() }
fn main() {
    var a: i64[>..<] = [3, 5, 7];
    print(a.pop(), ",", a.len, ",", a[1]);
    a.push(9);
    print(take_last(a), ",", a.len);
    clear_all(a);
    print(a.len);
    a.push(11);
    print(a[0], ",", a.len);
    var b: i8[>..<] = [127, -128];
    print(b.pop(), ",", b.len);
    b.clear(); b.push(5);
    print(b[0]);
    var x = 1;
    var refs: i64&[>..<] = [];
    refs.push(x);
    let held: i64& = refs.pop();
    held = 9;
    print(x, ",", refs.len);
    refs.push(x); refs.clear();
    print(x, ",", refs.len);
    var flags: bool[>..<] = [true];
    print(flags.pop(), ",", flags.len);
    var floats: f32[>..<] = [-0.0];
    print(floats.pop(), ",", floats.len);
}
