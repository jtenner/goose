fn same(a: i64[>..]&, b: i64[>..]&) -> bool { a == b }
fn optional_same(a: i64[2]?, b: i64[2]?) -> bool { a == b }
fn main() {
    var a: i64[2] = [1, 2]; var b: i64[2] = [1, 2];
    print(a == b, ",", a != b); b[1] = 9; print(a == b, ",", a != b);
    var limited_a: u8[..3] = [1, 2]; var limited_b: u8[..3] = [1, 2];
    print(limited_a == limited_b); limited_b.pop(); print(limited_a == limited_b);
    var growing_a: i64[>..] = [1, 2]; var growing_b: i64[>..] = [1, 2];
    print(growing_a == growing_b, ",", same(growing_a, growing_b)); growing_b.push(3); print(growing_a == growing_b, ",", same(growing_a, growing_b));
    var x: i64 = 4; var y: i64 = 4;
    var refs_a: i64&[2] = [x, a[0]]; var refs_b: i64&[2] = [x, a[0]];
    var refs_c: i64&[2] = [y, a[0]];
    print(refs_a == refs_b, ",", refs_a == refs_c);
    var f: f64[2] = [-0.0, 2.5]; var g: f64[2] = [0.0, 2.5];
    print(f == g); var zero: f64 = 0.0; f[1] = zero / zero; g[1] = zero / zero;
    print(f == g);
    var optional_a: i64[2]? = null; var optional_b: i64[2]? = null;
    print(optional_same(optional_a, optional_b)); optional_a .= a;
    print(optional_same(optional_a, optional_b)); optional_b .= b;
    print(optional_same(optional_a, optional_b)); optional_b .= a;
    print(optional_same(optional_a, optional_b));
    var single_a: f32[2] = [-0.0, 1.5]; var single_b: f32[2] = [0.0, 1.5];
    print(single_a == single_b);
    var bool_a: bool[2] = [true, false]; var bool_b: bool[2] = [true, false];
    print(bool_a == bool_b); bool_b[1] = true; print(bool_a == bool_b);
    var empty_a: i64[0] = []; var empty_b: i64[0] = []; print(empty_a == empty_b);
}
