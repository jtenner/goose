// warning: redundant &: value is passed by reference without it
// warning: redundant &: global is passed by reference without it
var global: i64 = 11;
fn update(x: i64&) { x += 4; }
recursive fn depth(n: i64) -> i64 {
    var local = n;
    let r = &local;
    if n > 0 { local += depth(n - 1); }
    update(r);
    return local;
}
fn main() {
    var a: i8 = 3;
    let r = &a;
    r += 2;
    print("alias=", a, ",", r);
    var value = 8;
    update(&value);
    print("call=", value);
    update(&global);
    print("global=", global);
    print("depth=", depth(100));
}
