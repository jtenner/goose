struct S{n:i64}
recursive fn make()->S{return S{n:7};}
var value:S=-make();
fn main(){assert(value.n == -7);print("global");}
