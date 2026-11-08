struct S{n:i64}
recursive fn read(p:S)->i64{defer{p.n=9;assert(p.n==9);}return p.n;}
fn main(){var s:S=S{n:2};assert(read(s)==2);assert(s.n==2);print("callee_defer");}
