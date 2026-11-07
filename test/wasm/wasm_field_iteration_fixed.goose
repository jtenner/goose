struct Cell { n: i64 }
struct Row { mark: u8, cells: Cell[2], numbers: i64[..4] }
fn main() {
    var row: Row = Row { mark: 9, cells: [Cell { n: 1 }, Cell { n: 2 }], numbers: [3, 4] };
    var total: i64 = 0;
    for cell, i in row.cells {
        if i == 0 { row.cells[0].n = 99; assert(cell.n == 1); }
        total += cell.n;
    }
    assert(total == 3);
    for &cell in row.cells { cell.n += 1; }
    for &number in row.numbers { number += 10; }
    assert(row.cells[0].n == 100); assert(row.cells[1].n == 3);
    assert(row.numbers[0] == 13); assert(row.numbers[1] == 14); assert(row.mark == 9);
    print("field-fixed");
}
