var calls:i64=0;recursive fn tick()->i64{calls++;print("eval");return calls;}
struct S{n:i64}
fn main(){var a:S[0]=[S{n:tick()};0];assert(calls==1);assert(a.len==0);print("live_zero");}
