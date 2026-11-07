var calls:i64=0;recursive fn tick()->i64{calls++;return calls;}
struct S{n:i64}
struct I{rows:S[2]}
struct H{groups:I[2]}
fn main(){var h:H=H{groups:[I{rows:[S{n:tick()};2]};2]};assert(calls==1);assert(h.groups[1].rows[0].n==1);assert(h.groups[0].rows[1].n==1);print("nested_fill");}
