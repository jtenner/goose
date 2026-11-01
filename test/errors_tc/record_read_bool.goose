// error: read_record_le field flag must be u8/u16/u32/u64 or i8/i16/i32/i64
struct Header { flag: bool }
fn main() { let record, ok = read_record_le<Header>(0, "a"); }
