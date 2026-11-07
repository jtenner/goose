struct Cell { n: i64 }
enum E { Big { n: i64 }, Small { n: u8 }, Empty }
struct Outer { first: Cell, bytes: u8[..3], value: E }
fn main() { var target: Outer = Outer { first: Cell { n: 1 }, bytes: [1], value: E.Big { n: 2 } }; target = Outer { first: Cell { n: 7 }, bytes: [3, 4], value: E.Small { n: 9 } }; assert(target.first.n == 7); assert(target.bytes.len == 2); assert(target.bytes[1] == 4); match target.value { Small p => assert(p.n == 9), _ => assert(false) } target.value = E.Empty; match target.value { Empty => {}, _ => assert(false) } print("nested"); }
