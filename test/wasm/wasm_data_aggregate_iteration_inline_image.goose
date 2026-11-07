struct S { bytes: u8[..3], mark: u8 }
fn main() {
 var rows: S[] = [S { bytes: [1], mark: 11 }, S { bytes: [2, 3], mark: 22 }];
 print("seed");
 for s, i in rows { assert(s.bytes.len == i + 1); assert(s.mark == (i + 1) * 11); print("inlinecopy"); }
}
