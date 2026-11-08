struct Row { cells: u16[2] }
recursive fn read(a: u16[2]&) -> i64 { a[1] }
fn main() { var rows: Row[varint] = [Row { cells: [11, 22] }]; print(read(rows[0].cells)); }
