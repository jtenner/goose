struct S{n:i64}
recursive fn make()->S{return{var s:S=S{n:7};s};}
fn main(){var s:S=make();assert(s.n==7);print("block");}
