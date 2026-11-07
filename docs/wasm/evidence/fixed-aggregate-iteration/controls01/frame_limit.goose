struct S { bytes: u8[2147483648] }
fn main() { var a: S[..1] = []; for s in a { assert(s.bytes[0] == 0); } print("limit"); }
