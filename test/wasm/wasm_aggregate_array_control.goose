struct S { mark: u8, n: u32, tail: u16 }
var seed: S = S { mark: 7, n: 305419896, tail: 65000 };
fn main() {
 var a: S[2] = [seed, seed];
 assert(a[0].mark == 7);
 assert(a[0].n == 305419896);
 assert(a[0].tail == 65000);
 assert(a[1].mark == 7);
 assert(a[1].tail == 65000);
 a[1].n = 99;
 assert(a[0].n == 305419896);
 assert(a[1].n == 99);
 print("control");
}
