fn echo(a: const u8[3]&) -> const u8[3]& { return a; }
fn main() {
    var a: u8[3] = "a\0b"; var b: u8[3] = copy(a); b[0] = 90;
    var c: u8[3] = copy(echo(a));
    var limited: u8[..8] = "hi"; var copied: u8[..8] = copy(limited); copied.push(33);
    var zero: u8[0] = []; var zero_copy: u8[0] = copy(zero);
    print(a, ",", b, ",", c, ",", limited, ",", copied, ",", zero_copy.len);
}
