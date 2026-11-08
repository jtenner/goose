struct S{n:i64}
recursive fn read(p:S)->i64{return p.n;}
var result:i64=read(S{n:7});
fn main(){assert(result==7);print("global_init");}
