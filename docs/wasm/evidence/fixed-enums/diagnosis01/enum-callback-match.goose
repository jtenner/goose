enum E { A { x: i64 }, B }
fn invoke<F>(e: E&) { F(e); }
fn main() { var e: E = E.A { x: 7 }; invoke(e) { p: E& => match p { A item => { var own: E.A = copy(item); own.x += 1; assert(own.x == 8); assert(item.x == 7); print(own.x); }, B => assert(false) } }; }
