struct Row { mark: u8, target: i64&, cells: u16[2], tail: u16 }
recursive fn read(cells: u16[2]&) -> i64 { cells[1] }
recursive fn select(rows: Row[]&) -> Row& { rows[1] }
struct PlainRow { mark: u8, cells: u16[2], tail: u16 }
recursive fn dynamic(seed: i64) -> i64 {
    var rows: PlainRow[] = [PlainRow { mark: 1, cells: [11, 22], tail: 60000 }];
    var copied: PlainRow[] = copy(rows);
    copied[0].cells[1] += 3;
    assert(rows[0].cells[1] == 22);
    return read(copied[0].cells);
}
fn main() {
    assert(dynamic(10) == 25);
    var x: i64[] = [10]; var y: i64[] = [20];
    var rows: Row[] = [Row { mark: 1, target: x[0], cells: [11, 22], tail: 60000 },
                      Row { mark: 2, target: y[0], cells: [33, 44], tail: 65000 }];
    assert(rows.len == 2); assert(read(rows[0].cells) == 22);
    var copied: Row[] = copy(rows);
    assert(copied .!= rows); copied[0].target += 7;
    assert(x[0] == 17); assert(rows[0].target == 17);
    var r: Row& = select(rows); r.cells[1] = 99;
    assert(rows[1].cells[1] == 99); assert(copied[1].cells[1] == 44);
    assert(r.tail == 65000);
    for &row in rows { row.mark += 1; }
    assert(rows[0].mark == 2); assert(rows[1].mark == 3);
    assert(dynamic(30) == 25);
    var empty: Row[] = []; var emptyCopy: Row[] = copy(empty);
    assert(empty.len == 0); assert(emptyCopy.len == 0); assert(empty .!= emptyCopy);
    print("data-rows=ok");
}
