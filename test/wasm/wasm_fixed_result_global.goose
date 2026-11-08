struct S{n:i64}
recursive fn make(n:i64)->S{S{n:n}}
var s:S=make(7);
fn main(){assert(s.n==7);print("global");}
