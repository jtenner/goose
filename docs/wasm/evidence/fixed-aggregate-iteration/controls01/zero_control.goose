struct S { mark: u8, n: u32, tail: u16 }
fn main() {
 var a: S[..1] = [];
 for s in a { assert(false); }
 print("empty");
}
