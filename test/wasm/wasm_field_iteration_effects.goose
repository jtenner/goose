struct Cell { n: i64 }
struct Row { cells: Cell[2] }
struct Holder { rows: Row[]& }
var calls: i64 = 0;
recursive fn choose(holder: Holder&, replacement: Row[]&) -> i64 {
    calls++; holder.rows .= replacement; return 0;
}
fn main() {
    var old: Row[] = [Row { cells: [Cell { n: 1 }, Cell { n: 2 }] }];
    var replacement: Row[] = [Row { cells: [Cell { n: 10 }, Cell { n: 20 }] }];
    var holder: Holder = Holder { rows: old }; var total: i64 = 0;
    for cell in holder.rows[choose(holder, replacement)].cells { total += cell.n; }
    assert(calls == 1); assert(total == 3); assert(holder.rows .== &replacement);
    print("field-effects");
}
