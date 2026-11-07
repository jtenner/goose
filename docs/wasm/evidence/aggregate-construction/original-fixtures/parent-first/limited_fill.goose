var calls:i64=0; recursive fn tick()->i64{calls++;return calls;}
struct S { n:i64 }
fn main(){var a:S[..3]=[S{n:tick()};2];assert(calls==1);assert(a.len==2);assert(a[1].n==1);print("limited_fill");}
