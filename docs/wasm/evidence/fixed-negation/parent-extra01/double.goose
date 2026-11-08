struct S{n:i64}
recursive fn make()->S{return S{n:7};}
fn main(){var s:S=-(-make());assert(s.n==7);print("double");}
