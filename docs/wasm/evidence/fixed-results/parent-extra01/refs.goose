struct S{link:i64&,n:i64}
recursive fn make(link:i64&,n:i64)->S{return S{link:link,n:n};}
recursive fn duplicate(p:S)->S{return p;}
fn main(){var values:i64[]=[7];var s:S=duplicate(make(values[0],9));assert(s.n==9);s.link++;assert(values[0]==8);assert(s.link .== &values[0]);print("refs");}
