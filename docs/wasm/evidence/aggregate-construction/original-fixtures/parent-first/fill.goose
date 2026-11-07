var calls:i64=0; recursive fn tick()->i64{calls++;return calls;}
struct S { n:i64 }
fn main(){var a:S[3]=[S{n:tick()};3];assert(calls==1);assert(a[0].n==1);assert(a[2].n==1);assert(&a[0] .!= &a[1]);print("fill");}
