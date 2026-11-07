struct Row { values: i64[2] }
var calls: i64 = 0;
recursive fn pick(row: Row&) -> Row& { calls++; return row; }
fn main() { var row: Row = Row { values: [1, 2] }; var total: i64 = 0; for n in pick(row).values { total += n; } assert(total == 3); assert(calls == 1); print("call-field"); }
