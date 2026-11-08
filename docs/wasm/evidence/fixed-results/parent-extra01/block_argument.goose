struct S{n:i64}
recursive fn read(p:S)->i64{return p.n;}
fn main(){assert(read({var s:S=S{n:7};defer{s.n=9;}s})==7);print("block_argument");}
