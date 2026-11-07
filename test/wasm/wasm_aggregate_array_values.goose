struct Cell { lead: u8, pad, word: u32, values: u16[2], tail: i16 }
struct Empty {}
fn main() {
 var a: Cell[2] = [Cell { lead: 7, word: 305419896, values: [11, 22], tail: -3 }, Cell { lead: 9, word: 17, values: [33, 44], tail: -4 }];
 assert(a.len == 2); assert(a[0].lead == 7); assert(a[0].word == 305419896); assert(a[0].values[1] == 22); assert(a[1].tail == -4);
 var b: Cell[2] = copy(a); b[0].values[1] = 99; assert(a[0].values[1] == 22); assert(b[0].values[1] == 99);
 var selected: Cell& = a[1]; selected.word += 5; assert(a[1].word == 22); assert(b[1].word == 17);
 var empty: Empty[2] = [Empty {}, Empty {}]; assert(&empty[0] .!= &empty[1]);
 var none: Cell[0] = []; assert(none.len == 0);
 print("values=", a[0].word, ",", b[0].values[1], ",", a[1].word);
}
