struct S { n: i64 }
var target: S = S { n: 1 };
var witness: i64 = { target = S { n: 8 }; target.n };
fn main() { assert(witness == 8); assert(target.n == 8); print("global"); }
