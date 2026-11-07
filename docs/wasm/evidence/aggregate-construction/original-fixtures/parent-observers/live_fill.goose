var calls:i64=0;recursive fn tick()->i64{calls++;print("eval");return calls;}
struct S{n:i64}
fn main(){var a:S[3]=[S{n:tick()};3];assert(calls==1);assert(a[2].n==1);print("live_fill");}
