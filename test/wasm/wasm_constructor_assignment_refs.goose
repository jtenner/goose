var seed: i64 = 1;
struct S { n: i64, link: i64& }
var target: S = S { n: 3, link: seed };
fn main() { target = S { n: 7, link: target.n }; assert(target.link .== &target.n); assert(target.link == 7); print("refs"); }
