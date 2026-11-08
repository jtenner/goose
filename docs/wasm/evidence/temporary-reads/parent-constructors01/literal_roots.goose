struct S{n:i64}
var calls:i64=0;recursive fn tick()->i64{calls++;return 7;}
fn main(){assert((S{n:tick()}).n==7);assert(([tick(),8])[1]==8);assert(default<i64[2]>().len==2);assert(calls==2);print("literal_roots");}
