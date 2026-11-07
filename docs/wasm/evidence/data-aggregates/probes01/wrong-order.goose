var trace: i64 = 0;
struct Holder { cells: u16[..3] }
struct Cell { values: u16[..3], empty: u8[..1], tag: u8 }
recursive fn tick(value: i64) -> i64 {
    trace = trace * 100 + value;
    var scratch: i64[] = [value]; assert(scratch[0] == value);
    return 7;
}
inline fn inner(value: i64) -> u16 {
    var holder: Holder = Holder { cells: [value as u16, (value + 1) as u16] };
    assert(holder.cells[0] == value); assert(holder.cells[1] == value + 1);
    return tick(value) as u16;
}
recursive fn work(early: bool) -> i64 {
    var rows: Cell[] = [Cell { values: [inner(2), inner(1)], empty: [tick(3) as u8; 0], tag: 4 },
                       Cell { values: [inner(5), inner(6)], empty: [tick(7) as u8; 0], tag: 8 }];
    defer {
        assert(rows[0].values.len == 2); assert(rows[1].values[1] == 7);
        assert(rows[0].empty.len == 0); assert(rows[1].empty.len == 0);
        trace = trace * 100 + 9;
    }
    var copied: Cell = copy(rows[0]); copied.values[0] = 19;
    assert(rows[0].values[0] == 7); assert(copied.values[0] == 19);
    if early { return copied.tag; }
    var index: i64 = 0;
    while index < rows.len {
        let saved = index;
        var scratch: i64[] = [saved];
        defer { assert(scratch[0] == saved); assert(rows[1].values[0] == 7); }
        if index == 0 { index++; continue; }
        break;
    }
    return rows[1].tag;
}
struct Partial { cells: u16[2] }
recursive fn partial(early: bool) -> i64 {
    var rows: Partial[] = [Partial { cells: [if early { return 5; } else { 7 as u16 }, 8] }];
    assert(rows[0].cells[0] == 7); assert(rows[0].cells[1] == 8);
    return 9;
}
fn main() {
    assert(work(true) == 4); assert(trace == 1020305060709);
    var keep: i64[] = [91];
    assert(partial(true) == 5); assert(partial(false) == 9); assert(keep[0] == 91);
    trace = 0; assert(work(false) == 8); assert(trace == 1020305060709); assert(keep[0] == 91);
    var index: i64 = 0;
    while index < 20 {
        trace = 0; assert(work(index % 2 == 0) == (if index % 2 == 0 { 4 } else { 8 }));
        assert(trace == 1020305060709); assert(keep[0] == 91); index++;
    }
    print("data-cleanup=ok");
}
