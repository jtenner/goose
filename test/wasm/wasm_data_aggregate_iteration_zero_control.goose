struct S { mark: u8, n: u32, tail: u16 }
recursive fn empty(rows: S[]&) {
 for s in rows { assert(false); }
 print("empty");
}
fn main() { var rows: S[] = []; empty(rows); }
