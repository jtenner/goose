struct S { mark: u8, n: i64, link: i64& }
struct Outer { value: S }
recursive fn set_value(dst: S&, old: i64&) { dst = S { mark: 7, n: old + 1, link: old }; }
fn main() {
 var x: i64[] = [10];
 var frame: S = S { mark: 1, n: 1, link: x[0] };
 var rows: S[] = [S { mark: 2, n: 2, link: x[0] }];
 var outer: Outer[] = [Outer { value: S { mark: 3, n: 3, link: x[0] } }];
 set_value(frame, x[0]); set_value(rows[0], x[0]); set_value(outer[0].value, x[0]);
 assert(frame.n == 11); assert(rows[0].mark == 7); assert(outer[0].value.n == 11);
 assert(frame.link .== &x[0]); assert(rows[0].link .== &x[0]);
 rows[0] = S { mark: 9, n: rows[0].n + 1, link: rows[0].n };
 assert(rows[0].n == 12); assert(rows[0].link .== &rows[0].n);
 outer[0].value = S { mark: 8, n: 19, link: rows[0].n };
 assert(outer[0].value.n == 19); assert(outer[0].value.link == 12);
 print("targets");
}
