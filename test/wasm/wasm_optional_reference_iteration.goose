fn main() {
    var a = 10;
    var refs: i64?[>..] = [];
    refs.push(null); refs.push(a);
    for &r in refs { if r { r += 1; } }
    print(a);
}
