struct S { n: i64 }
recursive fn big() -> i64 { var bytes: u8[70000] = [7; 70000]; assert(bytes[69999] == 7); return bytes[69999]; }
fn main() { var target: S = S { n: 1 }; target = S { n: big() }; assert(target.n == 7); print("growth"); }
