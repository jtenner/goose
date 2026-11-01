// Little-endian record snapshots own their values, including on failure.
struct Header { tag: u8, count: u32, delta: i16 }
fn load(at: i64, bytes: const u8[:]) -> Header, bool {
    return read_record_le<Header>(at, bytes);
}
fn main() {
    var bytes: u8[9] = [99, 7, 1, 2, 3, 4, 0, 128, 88];
    var h, ok = load(1, bytes);
    print(ok);
    print(h.tag);
    print(h.count);
    print(h.delta);
    bytes[1] = 0;
    print(h.tag);
    h.tag = 6;
    print(bytes[1]);
    let bad, short = load(3, bytes);
    print(short);
    print(bad.tag);
    print(bad.count);
    print(bad.delta);
    let last, exact = load(2, bytes);
    print(exact);
    print(last.tag);
}
