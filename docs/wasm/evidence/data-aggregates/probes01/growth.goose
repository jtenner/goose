recursive fn take() -> u8 { print("child"); var scratch: u8[] = [3]; return scratch[0]; }
struct Wide { tag: u8 = take(), bytes: u8[40000] = default<u8[40000]>() }
fn main() {
    print("ready");
    var rows: Wide[] = [Wide {}, Wide {}];
    assert(rows.len == 2); assert(rows[0].tag == 3); assert(rows[1].tag == 3);
    assert(rows[0].bytes[39999] == 0); assert(rows[1].bytes[39999] == 0);
    print("done");
}
