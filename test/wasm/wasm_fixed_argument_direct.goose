struct S{n:i64}
recursive fn alter(s:S)->i64{s.n=9;return s.n;}
fn main(){var a:S=S{n:2};assert(alter(a)==9);assert(a.n==2);print("direct");}
