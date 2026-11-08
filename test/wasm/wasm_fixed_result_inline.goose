struct S{n:i64}
inline fn make(n:i64)->S{S{n:n}}
fn main(){var s:S=make(7);assert(s.n==7);print("inline");}
