struct Item { n: i64 }
var large: Item[..65536] = [Item { n: 9 }];
fn main() {
 var a: Item[..3] = [Item { n: 1 }, Item { n: 2 }]; assert(a.len == 2); assert(a.cap == 3);
 for &e, i in a { e.n += i + 3; } assert(a[0].n == 4); assert(a[1].n == 6);
 var b: Item[..3] = copy(a); b[1].n += 10; assert(a[1].n == 6); assert(b[1].n == 16);
 a.clear(); assert(a.len == 0); assert(b.len == 2);
 var small: Item[..255] = [Item { n: 7 }]; var medium: Item[..256] = [Item { n: 8 }]; var wider: Item[..65535] = [Item { n: 10 }];
 assert(small[0].n == 7); assert(medium[0].n == 8); assert(wider[0].n == 10); assert(large[0].n == 9); assert(large.len == 1); assert(large.cap == 65536);
 print("limited=", b[0].n, ",", b[1].n);
}
