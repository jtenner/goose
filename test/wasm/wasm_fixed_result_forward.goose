struct S{n:i64}
recursive fn make(n:i64)->S{S{n:n}}
recursive fn forward(n:i64)->S{return make(n);}
fn main(){var s:S=forward(7);assert(s.n==7);print("forward");}
