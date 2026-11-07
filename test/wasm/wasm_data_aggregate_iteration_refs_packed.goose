struct Link { marker: u8, value: i64& }
fn main() {
 var live: i64[] = [91]; var x: i64[] = [10]; var y: i64[] = [20];
 var a: Link[] = [Link { marker: 7, value: x[0] }];
 for s in a { a[0].value .= y[0]; assert(s.value .== &x[0]); s.value += 1; assert(s.marker == 7); }
 assert(x[0] == 11); assert(y[0] == 20); assert(live[0] == 91); assert(a[0].value .== &y[0]);
 print("refs=", x[0], ",", y[0]);
}
