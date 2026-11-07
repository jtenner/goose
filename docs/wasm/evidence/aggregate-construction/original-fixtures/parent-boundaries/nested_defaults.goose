var calls:i64=0;recursive fn tick()->i64{calls++;print("eval");return calls;}
struct S{n:i64=tick()}
struct I{rows:S[2]=default<S[2]>()}
fn main(){var a:I[2]=default<I[2]>();assert(calls==4);assert(a[0].rows[0].n==1);assert(a[0].rows[1].n==2);assert(a[1].rows[0].n==3);assert(a[1].rows[1].n==4);print("nested_defaults");}
