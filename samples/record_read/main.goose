// A wire record is an eager snapshot with one recoverable extent check.
struct MemoryLimitRecord { minimum: u64, maximum: u64, flags: u32 }
fn main() {
    let bytes: u8[20] = [1,0,0,0,0,0,0,0, 8,0,0,0,0,0,0,0, 3,0,0,0];
    var limit, ok = read_record_le<MemoryLimitRecord>(0, bytes);
    if !ok { print("short memory-limit record"); return; }
    print(limit.minimum);
    print(limit.maximum);
    print(limit.flags);
    limit.flags = 0; // Changes this snapshot only.
}
