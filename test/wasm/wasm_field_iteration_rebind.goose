struct Cell { n: i64 }
struct Holder { rows: Cell[]& }
fn main() {
    var first: Cell[] = [Cell { n: 1 }, Cell { n: 2 }];
    var second: Cell[] = [Cell { n: 10 }, Cell { n: 20 }, Cell { n: 30 }];
    var holder: Holder = Holder { rows: first }; var total: i64 = 0;
    for cell, i in holder.rows {
        if i == 0 { holder.rows .= second; first[0].n = 99; assert(cell.n == 1); }
        total += cell.n;
    }
    assert(total == 51);
    for &cell, i in holder.rows { cell.n += 1; if i == 0 { holder.rows .= first; } }
    assert(second[0].n == 11); assert(first[1].n == 3);
    print("field-rebind");
}
