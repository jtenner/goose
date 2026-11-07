fn zero(a: const u8[0]&, b: const u8[0]&) {
    print("distinct=", a .!= b);
    print("zero=", a.len, ",", b.len);
}
fn main() {
    var empty_a: u8[0] = []; var empty_b: u8[0] = [];
    zero(empty_a, empty_b);
    var one: u8[..255] = []; var two: u8[..256] = [];
    for i in 255 { one.push(i as! u8); two.push(i as! u8); }
    two.push(255);
    print(one.len, ",", one[254], ",", two.len, ",", two[255]);
    var small: u8[..65535] = []; var large: u8[..65536] = [];
    for i in 65535 { small.push(i as! u8); large.push(i as! u8); }
    large.push(255);
    print(small.len, ",", small[65534], ",", large.len, ",", large[65535]);
    print(two.pop(), ",", two.len, ",", large.pop(), ",", large.len);
}
