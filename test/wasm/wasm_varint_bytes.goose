var calls: i64 = 0;
fn change(a: u8[varint]&) -> i64 { calls += 1; a[0] = 90; return calls; }
fn main() {
    var text: u8[varint] = "a\0b"; print(text, ",", change(text), ",", text);
    var repeated: u8[varint] = [65; 128]; print(repeated);
    var a: u8[varint] = [120; 70000]; var b: u8[varint] = copy(a); b[69999] = 121;
    print("large=", a.len, ",", a[69999], ",", b[69999]);
    var zero: u8[varint] = ""; print("zero=", zero.len, zero);
}
