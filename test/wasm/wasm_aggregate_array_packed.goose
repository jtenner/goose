struct Row { mark: u8, target: i64&, cells: u16[2], tail: u16 }
recursive fn read(cells: u16[2]&) -> i64 { cells[1] }
recursive fn get(rows: Row[2]&) -> Row& { rows[1] }
fn main() {
 var x: i64[] = [10]; var y: i64[] = [20];
 var rows: Row[2] = [Row { mark: 1, target: x[0], cells: [11, 22], tail: 60000 }, Row { mark: 2, target: y[0], cells: [33, 44], tail: 65000 }];
 assert(read(rows[0].cells) == 22); assert(read(get(rows).cells) == 44);
 var copied: Row[2] = copy(rows); copied[0].target += 7; assert(x[0] == 17); assert(rows[0].target == 17); assert(rows[1].target == 20);
 var r: Row& = get(rows); r.cells[1] = 99; assert(rows[1].cells[1] == 99); assert(copied[1].cells[1] == 44); assert(r.tail == 65000);
 var refs: Row&[] = [rows[0], rows[1]]; refs[0].mark += 4; assert(rows[0].mark == 5);
 print("packed=", x[0], ",", y[0], ",", read(r.cells));
}
