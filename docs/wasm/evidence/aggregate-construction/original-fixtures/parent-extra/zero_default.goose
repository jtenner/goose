var calls:i64=0;recursive fn tick()->i64{calls++;return calls;}
struct S{n:i64=tick()}
fn main(){var a:S[0]=default<S[0]>();assert(a.len==0);assert(calls==0);print("zero_default");}
