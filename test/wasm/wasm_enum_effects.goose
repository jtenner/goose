struct Cell { n: i64 }
var counter: i64 = 0; fn tick() -> i64 { counter++; return counter; }
enum Build { Pair { first: Cell, a: i64 = tick(), middle: i64, b: i64 = tick() }, None }
var left: Cell = Cell { n: 10 }; var right: Cell = Cell { n: 200 }; var selected: Cell& = left;
fn change() -> i64 { left.n = 77; return 9; } fn redirect() -> i64 { selected .= right; return 3; }
fn main() {
 var b: Build = Build.Pair { first: left, middle: change() };
 match b { Pair p => { assert(p.first.n == 10); assert(p.middle == 9); assert(p.a == 1); assert(p.b == 2); }, None => assert(false) }
 selected.n += redirect(); assert(left.n == 80); assert(right.n == 200); assert(selected.n == 200);
 var v: Build.Pair = Build.Pair { first: left, middle: 5 }; var p: Build.Pair& = v;
 var got: i64 = &p.middle; assert(got == 5); p.middle += 2; assert(v.middle == 7); assert(v.a == 3); assert(v.b == 4);
 print("order=", counter);
}
