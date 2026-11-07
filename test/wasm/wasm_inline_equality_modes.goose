fn main() {
    var a: i64 = 3; var b: i64 = 3;
    var x: i64&[2] = [a, b]; var y: i64&[2] = [a, b]; var z: i64&[2] = [b, a];
    print(x == y, ",", x == z);
    x[0] += 1; print(a, ",", b);
    var ox: i64?[2] = [null, a]; var oy: i64?[2] = [null, a];
    print(ox == oy); oy[1] .= b; print(ox == oy);
    var first: i64[1] = [9]; var second: i64[1] = [9];
    var ax: i64[1]&[2] = [first, second]; var ay: i64[1]&[2] = [first, second];
    var az: i64[1]&[2] = [second, first];
    print(ax == ay, ",", ax == az);
    var optional_a: i64[1]?[2] = [null, first]; var optional_b: i64[1]?[2] = [null, first];
    print(optional_a == optional_b); optional_b[1] .= second; print(optional_a == optional_b);
    var zero: f32 = 0.0; var nan: f32 = zero / zero;
    var floating: f32[1] = [nan]; var other_floating: f32[1] = [nan];
    print(floating == floating, ",", floating != floating, ",", floating == other_floating);
}
