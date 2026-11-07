fn main() {
    var a = 10;
    var b = 20;
    var refs: i64&[>..] = [];
    refs.push(a); refs.push(b);
    for r in refs { r += 1; }
    print(a, ",", b);
    for &r in refs { r += 1; }
    print(a, ",", b);
}
