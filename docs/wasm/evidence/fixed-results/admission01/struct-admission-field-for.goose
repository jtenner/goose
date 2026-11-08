struct S { x: i64 }
struct Outer { items: i64[2] }
fn main() { var a: Outer = Outer { items: [1, 2] }; for v in a.items { print(v); } }
