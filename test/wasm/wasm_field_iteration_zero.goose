struct Cell { n: i64 }
struct Row { cells: Cell[..2] }
var calls: i64 = 0;
recursive fn choose() -> i64 { calls++; return 0; }
fn main() {
    var rows: Row[1] = [Row { cells: [] }];
    for cell in rows[choose()].cells { assert(false); }
    assert(calls == 1); print("field-zero");
}
