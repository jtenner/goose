struct S{n:i64}
recursive fn make(n:i64)->S{return S{n:n};}
fn main(){var s:S=make(7);assert(s.n==7);print("direct");}
