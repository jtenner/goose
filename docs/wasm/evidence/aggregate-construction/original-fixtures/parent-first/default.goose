var calls: i64=0; recursive fn tick()->i64 { calls++; return calls; }
struct S { n:i64=tick() }
fn main(){ var a:S[3]=default<S[3]>(); assert(calls==3); assert(a[0].n==1);assert(a[1].n==2);assert(a[2].n==3);print("default");}
