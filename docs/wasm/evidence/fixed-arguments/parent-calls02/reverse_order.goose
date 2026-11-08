struct S{n:i64}
var value:i64=7;var original:S=S{n:1};recursive fn mutate()->S&{value=12;return &original;}
recursive fn read(x:i64,p:S)->i64{return x+p.n;}
fn main(){assert(read(value,copy(mutate()))==8);assert(value==12);print("reverse_order");}
