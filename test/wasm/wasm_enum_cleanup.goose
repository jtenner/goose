enum Big { Data { bytes: u8[70000] }, Empty }
fn read(e: Big&, early: bool) -> i64 {
 var result: i64 = 0;
 match e { Data p => { defer { assert(p.bytes[69999] == 7); var scratch: i64[] = [9]; assert(scratch[0] == 9); print("defer"); } if early { return p.bytes[69999]; } result = p.bytes[69999]; }, Empty => assert(false) }
 return result;
}
fn main() {
 var b: Big = Big.Data { bytes: [7; 70000] }; assert(read(b, true) == 7); assert(read(b, false) == 7);
 for i in 3 { match b { Data p => { defer { print("loop=", i, ",", p.bytes[0]); } if i == 0 { continue; } if i == 1 { break; } }, Empty => assert(false) } }
 print("cleanup");
}
