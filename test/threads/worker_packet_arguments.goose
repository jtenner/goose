// runtime-debug: packed worker arguments preserve counts and private copies.
struct Prefix1 { tag: u8 }
struct Prefix3 { tag: u8, extra: u8[2] }
struct Prefix8 { tag: u8, extra: u8[7] }
struct Bag { tag: u8, bytes: u8[>..] }
struct Empty {}

fn check(p, bytes: u8[>..]&, bag: Bag&,
         words: u8[varint][>..]&, empty: Empty[>..]&, zero: Empty) {
    assert(p.tag == 7);
    assert(bytes.len == bag.bytes.len);
    for i in bytes.len { assert(bytes[i] == (i + 1) as u8); }
    assert(bag.tag == 9);
    for i in bag.bytes.len { assert(bag.bytes[i] == bytes[i]); }
    assert(words.len == 2);
    for word, i in words { assert(word == (if i == 0 { "a" } else { "odd" })); }
    assert(empty.len == 3);
    bytes.push(42);
    bag.bytes.push(43);
    words.push("private");
    empty.push(zero);
    assert(empty.len == 4);
    assert(bytes[bytes.len - 1] == 42 && bag.bytes[bag.bytes.len - 1] == 43);
}
thread_fn worker1(p: Prefix1, var bytes: u8[>..], var bag: Bag,
                  var words: u8[varint][>..], var empty: Empty[>..], zero: Empty) {
    check(p, bytes, bag, words, empty, zero);
}
thread_fn worker3(p: Prefix3, var bytes: u8[>..], var bag: Bag,
                  var words: u8[varint][>..], var empty: Empty[>..], zero: Empty) {
    check(p, bytes, bag, words, empty, zero);
}
thread_fn worker8(p: Prefix8, var bytes: u8[>..], var bag: Bag,
                  var words: u8[varint][>..], var empty: Empty[>..], zero: Empty) {
    check(p, bytes, bag, words, empty, zero);
}
fn exercise<W>(p) {
    for n in 0..6 {
        var bytes: u8[>..] = [];
        for i in n { bytes.push((i + 1) as u8); }
        var bag = Bag { tag: 9, bytes: copy(bytes) };
        var words: u8[varint][>..] = ["a", "odd"];
        var empty: Empty[>..] = [Empty {}, Empty {}, Empty {}];
        for repeat in 3 {
            assert(thread_wait(thread_spawn(W, p, copy(bytes), copy(bag),
                                            copy(words), copy(empty), Empty {})));
            assert(thread_wait(thread_spawn_contained(W, p, copy(bytes), copy(bag),
                                                      copy(words), copy(empty), Empty {})));
            assert(bytes.len == n && bag.bytes.len == n);
            assert(words.len == 2 && empty.len == 3);
            for word, i in words { assert(word == (if i == 0 { "a" } else { "odd" })); }
        }
    }
}
fn main() {
    exercise(Prefix1 { tag: 7 }, worker1);
    exercise(Prefix3 { tag: 7, extra: [11, 12] }, worker3);
    exercise(Prefix8 { tag: 7, extra: [1, 2, 3, 4, 5, 6, 7] }, worker8);
    print("worker packet arguments passed");
}
