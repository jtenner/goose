// runtime-debug: aliases and effects survive fixed arithmetic adaptation.
var source: i64[2] = [7, -8];
recursive fn later() -> i64[2] { source[0] = 99; return [3, 4]; }
recursive fn adapted(a: i64[2], depth: i64) -> i64[..3] {
    if depth != 0 { return adapted(a, depth - 1); }
    return -a;
}
fn invoke<F>() -> i64[..3] { return F(); }
struct Vector { x: i64, y: i64 }
struct Variable { tag: varint, values: i64[] }
fn main() {
    let result: i64[..3] = source + later();
    assert(result.len == 2);
    assert(result[0] == 10 && result[1] == -4);
    assert(source[0] == 99);
    let recursion = adapted([7, -8], 3);
    assert(recursion.len == 2 && recursion[0] == -7 && recursion[1] == 8);
    let callback = invoke() { -source };
    assert(callback.len == 2 && callback[0] == -99 && callback[1] == 8);
    var large: i64[600] = [7; 600];
    let big: i64[..601] = -large;
    assert(big.len == 600);
    for x in big { assert(x == -7); }
    let vectors: Vector[2] = [Vector { 1, 2 }, Vector { 3, 4 }];
    let negated: Vector[..3] = -vectors;
    assert(negated.len == 2 && negated[0].x == -1 && negated[1].y == -4);
    let summed: Vector[..3] = vectors + vectors;
    assert(summed.len == 2 && summed[0].y == 4 && summed[1].x == 6);
    let nested: i64[2][2] = [[1, 2], [3, 4]];
    let n: i64[2][..3] = -nested;
    assert(n.len == 2 && n[0][1] == -2 && n[1][0] == -3);
    var runtime: i64[..] = [..4];
    runtime = -source;
    assert(runtime.cap == 4 && runtime.len == 2);
    assert(runtime[0] == -99 && runtime[1] == 8);
    runtime = source + source;
    assert(runtime.cap == 4 && runtime.len == 2 && runtime[0] == 198);
    let variable = Variable { 300, -source };
    assert(variable.tag == 300 && variable.values.len == 2);
    assert(variable.values[0] == -99 && variable.values[1] == 8);
    var narrow: i8[2] = [7, -8];
    let small: i8[..3] = -narrow;
    assert(small.len == 2 && small[0] == -7 && small[1] == 8);
    let smallsum: i8[..3] = narrow + narrow;
    assert(smallsum.len == 2 && smallsum[0] == 14 && smallsum[1] == -16);
    var floats: f32[2] = [1.25, -2.5];
    let f: f32[..3] = -floats;
    assert(f.len == 2 && f[0] == -1.25 && f[1] == 2.5);
    let fs: f32[..3] = floats + floats;
    assert(fs.len == 2 && fs[0] == 2.5 && fs[1] == -5.0);
    print("fixed_math_lifetimes");
}
