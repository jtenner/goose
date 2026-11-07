fn bump(a: i64[varint]&) -> i64[varint]& {
    var scratch: u8[varint] = [99; 128]; a[0] += scratch[0]; return a;
}
fn main() {
    var a: i64[varint] = [1, 2, 3]; var b: i64[varint] = [4; 128];
    var r: i64[varint]& = a; var total: i64 = 0;
    for x, i in r { total += x; if i == 0 { r .= b; } }
    print("rebind=", total);
    var holders: i64[varint]&[varint] = [a];
    total = 0;
    for x, i in holders[0] { total += x; if i == 0 { holders[0] .= b; } }
    print("path=", total);
    var copied: i64[varint] = copy(bump(a));
    print("call=", a[0], ",", copied[0]);
    var optional: i64[varint]? = null; optional .= a;
    if optional != null { var c: i64[varint] = copy(optional); print("optional=", c.len, ",", c[0]); }
    var scalar: i64 = 7; var refs: i64&[varint] = [scalar; 128];
    var refs2: i64&[varint] = copy(refs); refs2[127] += 3;
    assert(refs[0] .== refs2[127]); print("refs=", scalar, ",", refs.len);
}
