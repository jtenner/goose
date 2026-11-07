fn main() { var a: u8[3] = [1, 2, 3]; var refs: u8[3]&[1] = [a]; var b: u8[..4] = refs[0]; print(b.len, ",", b[0]); }
