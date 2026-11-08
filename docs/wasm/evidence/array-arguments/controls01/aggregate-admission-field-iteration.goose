struct S { x: i64 = 7 }
struct H { items: S[1] }
fn main() { var h: H = H { items: [S { x: 1 }] }; for &s in h.items { print(s.x); } }
