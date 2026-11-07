struct Cell { n: i64 }
struct Box { value: Cell, after: i64 }
var source: Cell = Cell { n: 10 }; var calls: i64 = 0;
fn change() -> i64 { source.n = 99; return 5; }
fn index() -> i64 { calls++; return 1; }
fn rhs() -> i64 { calls++; return 7; }
fn main() {
 var rows: Box[2] = [Box { value: source, after: change() }, Box { value: source, after: 6 }];
 assert(rows[0].value.n == 10); assert(rows[0].after == 5); assert(rows[1].value.n == 99);
 rows[index()].value.n += rhs(); assert(calls == 2); assert(rows[1].value.n == 106);
 var a: Cell[2] = [source, Cell { n: change() }]; assert(a[0].n == 99); assert(a[1].n == 5);
 print("effects=", calls, ",", rows[0].value.n, ",", rows[1].value.n);
}
