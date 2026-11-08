struct S{n:i64}
recursive fn make(n:i64)->S{if n==0{return S{n:1};}var s:S=make(n-1);return S{n:s.n+n};}
fn main(){var s:S=make(9);assert(s.n==46);print("recursion");}
