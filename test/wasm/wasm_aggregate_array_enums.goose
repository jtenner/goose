enum E { Data { n: i64, items: u8[2] }, Empty, Other { n: u8 } }
fn main() {
 var a: E[3] = [E.Data { n: 11, items: [1, 2] }, E.Empty, E.Other { n: 9 }];
 var b: E[3] = copy(a);
 match b[0] { Data p => { assert(p.n == 11); assert(p.items[1] == 2); var own: E.Data = copy(p); own.n = 99; assert(p.n == 11); }, _ => assert(false) }
 match a[1] { Empty => {}, _ => assert(false) }
 match a[2] { Other p => assert(p.n == 9), _ => assert(false) }
 var payloads: E.Data[2] = [E.Data { n: 3, items: [4, 5] }, E.Data { n: 6, items: [7, 8] }];
 payloads[1].n += 1; assert(payloads[1].n == 7);
 for &e in a { match e { Data p => assert(p.n == 11), Empty => {}, Other p => assert(p.n == 9) } }
 print("enums");
}
