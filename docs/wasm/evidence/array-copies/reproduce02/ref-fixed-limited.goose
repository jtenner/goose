fn main() { var a: u8[3] = [1, 2, 3]; var r: u8[3]& = a; var b: u8[..4] = r; print(b.len, ",", b[0]); }
