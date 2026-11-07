struct Cell { n: i64 }
struct S { values: Cell[..2] }
fn main() { var old: Cell = Cell { n: 7 }; var target: S = S { values: [Cell { n:1 },Cell { n:2 }] }; target = S { values: [old,target.values[0]] }; assert(target.values[0].n == 7); assert(target.values[1].n == 1); print("array_copies"); }
