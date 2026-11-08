struct S{n:i64}
recursive fn make()->S{return S{n:7};}
var n:i64=make().n;
fn main(){assert(n==7);print("global");}
