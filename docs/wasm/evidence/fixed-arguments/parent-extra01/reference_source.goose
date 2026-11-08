struct S{n:i64}
var value:S=S{n:7};recursive fn source()->S&{return &value;}
recursive fn read(p:S)->i64{p.n++;return p.n;}
fn main(){assert(read(copy(source()))==8);assert(value.n==7);print("reference_source");}
