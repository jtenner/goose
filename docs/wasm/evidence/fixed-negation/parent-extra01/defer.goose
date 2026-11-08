struct S{n:i64}
var calls:i64=0;recursive fn make()->S{var s:S=S{n:7};defer{s.n=99;calls++;}return s;}
fn main(){var s:S=-make();assert(s.n == -7);assert(calls==1);print("defer");}
