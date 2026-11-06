fn bump(x: i64) -> i64 { return x * 3 + 1; }
fn choose(x: i64) -> i64 { if x < 0 { return -x; } return x + 2; }
fn main() {
    var x: i8 = 127;
    x += 1;
    print("wrap=", x);
    var u: u8 = 255;
    u += 1;
    print("unsigned=", u);
    var shift: i8 = -7;
    var count = 10;
    print("shift=", shift >> count, ",", shift << count);
    var a = -7;
    var b = -3;
    print("mod=", a % b, ",", a / b);
    var min = -9223372036854775808;
    var minusone = -1;
    print("edge=", min % minusone, ",", a % min);
    print("call=", bump(choose(-4)));
    var f: f32 = 0.1;
    var d = 1.0e-5;
    print("float=", f, ",", d, ",", -0.0, ",", 1.25 % 0.5);
    var wide = 18446744073709551615;
    print("u64=", wide, ",", wide / 3);
    print("casts=", (300 as! u8) as i64, ",", -3.75 as! i16);
}
