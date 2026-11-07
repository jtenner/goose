enum E { Value { n: i64 }, Empty }
fn main() { var a: E.Value = E.Value { n: 1 }; var b: E.Value = E.Value { n: 9 }; a = copy(b); a.n += 1; assert(a.n == 10); assert(b.n == 9); print("variant"); }
