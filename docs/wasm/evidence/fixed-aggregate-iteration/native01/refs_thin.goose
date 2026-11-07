struct Link { marker: u8, value: i64& }
fn main() {
 var x: i64 = 10; var y: i64 = 20;
 var a: Link[1] = [Link { marker: 7, value: x }];
 for s in a { a[0].value .= y; assert(s.value .== &x); s.value += 1; assert(s.marker == 7); }
 assert(x == 11); assert(y == 20); assert(a[0].value .== &y);
 print("refs=", x, ",", y);
}
