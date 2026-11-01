// parse-only: packed words preserve bit descriptors and both conditional branches.
enum Kind { Object, Array }
packed word Header : u64 {
    marked: bool,
    age: u2 = 1,
    kind: Kind,
    const if true {
        const if false { excluded: u129 } else { _: u21 },
    } else { _: u21 },
    _: u7,
    type_id: u32,
}
packed word Empty : u8 {}
packed word Full : u64 { value: u64 }
fn word(packed: u64) -> u64 { packed }
