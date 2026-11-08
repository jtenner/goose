struct S{n:i64}
inline fn make(n:i64)->S{if n==0{return S{n:3};}return S{n:n};}
fn main(){assert(make(0).n==3);assert(make(7).n==7);print("inline_field");}
