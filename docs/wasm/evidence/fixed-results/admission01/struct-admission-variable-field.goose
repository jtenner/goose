struct S { x: i64 }
struct V { data: i64[] }
fn main() { var a: V = V { data: [1] }; print(a.data[0]); }
