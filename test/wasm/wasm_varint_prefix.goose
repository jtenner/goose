var anchor: u8[varint] = [65; 128];
recursive fn inspect(a: i64[varint]&) -> i64 {
    var b: i64[varint] = copy(a); b[0] += 100;
    return b.len + b[0];
}
fn main() {
    var empty: u8[varint] = []; print("empty=", empty.len);
    var a: i64[varint] = [1, 2, 3]; var b: i64[varint] = copy(a); b[1] = 9;
    print("copy=", a[1], ",", b[1], ",", inspect(a));
    var small: u8[varint] = [7; 127]; var medium: i16[varint] = [8; 128];
    var wide: i16[varint] = [9; 16384];
    print("counts=", small.len, ",", medium.len, ",", wide.len, ",", wide[16383]);
    var other: i16[varint] = copy(wide); other[16383] = 10;
    print("last=", wide[16383], ",", other[16383], ",", wide == other);
    var floats: f32[varint] = [-0.0; 128]; print(floats.len, ",", floats[127]);
    var bits: bool[varint] = [true; 128]; print(bits.len, ",", bits[127]);
    print("anchor=", anchor.len, ",", anchor[127]);
}
