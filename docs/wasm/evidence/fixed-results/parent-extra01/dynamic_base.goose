struct S{n:i64}
recursive fn make(n:i64)->S{var a:i64[]=[n];return S{n:a[0]};}
fn main(){var a:S=make(7);assert(a.n==7);{var live:i64[]=[9];var b:S=make(8);assert(b.n==8);assert(live[0]==9);}print("dynamic_base");}
