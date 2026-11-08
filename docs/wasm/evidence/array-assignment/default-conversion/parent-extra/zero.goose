var calls:i64=0;recursive fn tick()->i64{calls++;return calls;}
struct S{n:i64=tick()}
fn main(){var a:S[..3]=default<S[0]>();var b:S[..4]=default<S[..2]>();assert(a.len==0);assert(b.len==0);assert(calls==0);print("zero");}
