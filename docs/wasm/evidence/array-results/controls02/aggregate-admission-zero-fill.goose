var calls: i64 = 0; fn tick() -> i64 { calls++; return calls; }
struct S { x: i64 = 7 }
fn main() { var a: S[0] = [S { x: tick() }; 0]; assert(calls == 1); print(a.len); }
