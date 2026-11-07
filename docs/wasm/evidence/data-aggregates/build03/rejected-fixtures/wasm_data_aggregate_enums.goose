enum Entry { Value { mark: u8, cells: u16[2], tail: u16 }, None }
struct Box { before: u8, entries: Entry[2], tail: u8 }
var globalRows: Box[] = [Box { before: 3, entries: [Entry.None, Entry.Value { mark: 4, cells: [5, 6], tail: 60000 }], tail: 7 }];
recursive fn check(rows: Box[]&) -> i64 {
    assert(rows[0].before == 3); assert(rows[0].tail == 7);
    match rows[0].entries[0] { None => {}, Value p => assert(false) }
    match rows[0].entries[1] { Value p => { assert(p.mark == 4); assert(p.cells[1] == 6); assert(p.tail == 60000); }, None => assert(false) }
    return rows.len;
}
fn main() {
    assert(check(globalRows) == 1);
    var copied: Box[] = copy(globalRows); assert(check(copied) == 1);
    var entries: Entry[] = [Entry.Value { mark: 1, cells: [2, 3], tail: 65000 }, Entry.None];
    var duplicate: Entry[] = copy(entries);
    match duplicate[0] { Value p => { assert(p.cells[0] == 2); assert(p.tail == 65000); }, None => assert(false) }
    match duplicate[1] { None => {}, Value p => assert(false) }
    assert(check(globalRows) == 1);
    print("data-enums=ok");
}
