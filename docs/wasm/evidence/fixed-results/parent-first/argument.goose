struct S{n:i64}
recursive fn make()->S{S{n:7}}
recursive fn read(s:S)->i64{return s.n;}
fn main(){assert(read(make())==7);print("argument");}
