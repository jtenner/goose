struct S { mark: u8, n: i64, target: i64&, tail: u16 }
struct Outer { value: S }
fn main() { var x: i64[] = [10]; var y: i64[] = [20]; var a: S[] = [S { mark: 1, n: 11, target: x[0], tail: 50001 }]; var b: S[] = [S { mark: 2, n: 22, target: y[0], tail: 60002 }]; b[0] = a[0]; assert(b[0].mark == 1); assert(b[0].n == 11); assert(b[0].tail == 50001); assert(b[0].target .== &x[0]); b[0].target += 1; assert(x[0] == 11); assert(y[0] == 20); var outer: Outer[] = [Outer { value: a[0] }]; outer[0].value = b[0]; assert(outer[0].value.n == 11); print("data"); }
