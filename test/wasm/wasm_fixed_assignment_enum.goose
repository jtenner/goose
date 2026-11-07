enum E { Big { n: i64 }, Small { n: u8 }, Empty }
fn main() { var a: E = E.Big { n: 1000 }; var b: E = E.Small { n: 7 }; var c: E = E.Empty; a = b; match a { Small p => assert(p.n == 7), _ => assert(false) } b = c; match b { Empty => {}, _ => assert(false) } print("enum"); }
