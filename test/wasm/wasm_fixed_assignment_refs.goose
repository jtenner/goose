struct S { n: i64 }
fn main() { var a: S = S { n: 1 }; var b: S = S { n: 2 }; var ref: S& = a; ref = b; assert(a.n == 2); assert(ref .== &a); var refs: S&[1] = [a]; refs[0] = b; assert(refs[0] .== &a); assert(a.n == 2); var rows: S[] = [S { n: 7 }]; ref .= rows[0]; ref = b; assert(rows[0].n == 2); print("refs"); }
