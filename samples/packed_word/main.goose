// goose++ build --cc gcc samples/packed_word/main.goose -o /tmp/packed-word
// Expected output: 2, true, 42 (one per line).
enum Kind { Object, Array, String }
packed word Header : u64 {
    marked: bool,
    age: u2,
    kind: Kind,
    _: u27,
    type_id: u32,
}
fn main() {
    var h = Header { false, 2, Kind.Array, 42 };
    h.marked = true;
    let raw = h as u64;
    let copy = raw as Header;
    assert(copy == h);
    print(copy.age);
    print(copy.marked);
    print(copy.type_id);
}
