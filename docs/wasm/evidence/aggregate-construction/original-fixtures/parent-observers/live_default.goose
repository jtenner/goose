var calls:i64=0;recursive fn tick()->i64{calls++;print("eval");return calls;}
struct S{n:i64=tick()}
fn main(){var a:S[3]=default<S[3]>();assert(calls==3);assert(a[2].n==3);print("live_default");}
