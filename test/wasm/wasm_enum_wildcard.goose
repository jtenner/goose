enum E { A { n: i64 }, B }
var original: E = E.A { n: 11 };
fn main() { match original { A p => { assert(p.n == 11); print("active"); }, _ => print("wildcard") } }
