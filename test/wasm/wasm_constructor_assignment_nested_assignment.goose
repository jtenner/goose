struct S { a: i64, b: i64 }
var outer: S = S { a:1,b:2 };
var inner: S = S { a:3,b:4 };
fn main() { outer = S { a:9, b: { inner = S { a:7, b: { assert(outer.a == 1); print("nested-live"); outer.a } }; assert(inner.a == 7); assert(inner.b == 1); assert(outer.a == 1); print("nested-done"); 8 } }; assert(outer.a == 9); assert(outer.b == 8); assert(inner.b == 1); print("nested_assignment"); }
