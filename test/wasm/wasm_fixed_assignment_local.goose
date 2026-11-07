struct S { mark: u8, n: i64, tail: u16 }
var global_value: S = S { mark: 1, n: 10, tail: 50001 };
fn main() { var a: S = S { mark: 2, n: 20, tail: 60002 }; var b: S = S { mark: 3, n: 30, tail: 40003 }; a = b; a.n += 1; assert(b.n == 30); assert(a.mark == 3); assert(a.tail == 40003); global_value = a; assert(global_value.n == 31); a = a; assert(a.n == 31); print("local"); }
