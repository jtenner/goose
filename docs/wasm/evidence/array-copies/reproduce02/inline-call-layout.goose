inline fn pick(a: u8[3]&) -> u8[3]& { return a; } fn main() { var a: u8[3] = [1, 2, 3]; var b: u8[..4] = pick(a); print(b.len, ",", b[0]); }
