struct Cell { n: i64 }
struct Row { mark: u8, cells: Cell[2] }
var calls: i64 = 0;
recursive fn choose() -> i64 { calls++; return 1; }
fn main() {
    var rows: Row[] = [Row { mark: 1, cells: [Cell { n: 1 }, Cell { n: 2 }] },
                      Row { mark: 2, cells: [Cell { n: 10 }, Cell { n: 20 }] }];
    var total: i64 = 0;
    for cell, i in rows[choose()].cells {
        if i == 0 { rows[1].cells[0].n = 99; assert(cell.n == 10); }
        total += cell.n;
    }
    assert(calls == 1); assert(total == 30); assert(rows[0].cells[0].n == 1);
    print("field-index");
}
