struct Item { n: i64, bytes: u8[2] }
struct Holder { before: u8, fixed: Item[2], limited: Item[..3], after: u16 }
recursive fn value(a: Item[2]&) -> i64 { a[1].n }
fn main() {
 var h: Holder = Holder { before: 7, fixed: [Item { n: 1, bytes: [2, 3] }, Item { n: 4, bytes: [5, 6] }], limited: [Item { n: 8, bytes: [9, 10] }], after: 65000 };
 assert(value(h.fixed) == 4); assert(h.limited.len == 1); assert(h.limited[0].bytes[1] == 10);
 var own: Item[2] = copy(h.fixed); own[1].n = 99; assert(h.fixed[1].n == 4);
 var copyOfH: Holder = copy(h); copyOfH.fixed[0].bytes[0] = 55; assert(h.fixed[0].bytes[0] == 2);
 var selected: Item[2]& = h.fixed; for &e in selected { e.n += 3; } assert(h.fixed[0].n == 4); assert(h.fixed[1].n == 7);
 assert(h.before == 7); assert(h.after == 65000); print("fields=", value(h.fixed), ",", own[1].n);
}
