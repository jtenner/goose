struct Cell { n: i64, bytes: u8[2] }
struct Row { mark: u8, cells: Cell[2], tail: u16 }
enum E { Rows { rows: Row[2] }, None }
recursive fn read(a: Cell[2]&) -> i64 { a[1].n }
fn main() {
 var live: i64[] = [9];
 var row: Row = Row { mark: 7, cells: [Cell { n: 1, bytes: [2, 3] }, Cell { n: 2, bytes: [4, 5] }], tail: 65000 };
 var values: E[2] = [E.Rows { rows: [row, row] }, E.None];
 var refs: E&[] = [values[0], values[1]];
 match refs[0] {
  Rows p => {
   assert(p.rows[0].cells[0].bytes[1] == 3); assert(p.rows[1].tail == 65000);
   var own: E.Rows = copy(p); own.rows[1].cells[1].n += 100; assert(p.rows[1].cells[1].n == 2); assert(read(own.rows[1].cells) == 102);
   var selected: Row[2]& = own.rows; for &r in selected { r.cells[0].n += 3; }
   assert(own.rows[0].cells[0].n == 4); assert(own.rows[1].cells[0].n == 4); assert(p.rows[0].cells[0].n == 1);
  },
  None => assert(false)
 }
 match values[1] { None => {}, _ => assert(false) }
 assert(live[0] == 9); print("nested");
}
