fn main() { var a: u8[..4] = [1, 2, 3]; var r: u8[..4]& = a; var b: u8[..8] = r; print(b.len, ",", b[0]); }
