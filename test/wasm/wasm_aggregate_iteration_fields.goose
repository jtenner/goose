var calls: i64 = 0;
fn tick() -> i64 { calls++; return 7; }
struct Cell { n: i64 = tick(), data: u8[..300] }
struct Row { cells: Cell[2], mark: u8 }
fn main() {
 var rows: Row[1] = [Row { cells: [Cell { data: [1, 2] }, Cell { data: [3, 4] }], mark: 9 }];
 assert(calls == 2);
 for row in rows {
  rows[0].cells[0].n += 100; assert(row.cells[0].n == 7);
  let selected .= row.cells; var sum: i64 = 0;
  for cell in selected { sum += cell.n; assert(cell.data.len == 2); }
  assert(sum == 14); assert(row.mark == 9);
 }
 assert(calls == 2); print("fields=", calls);
}
