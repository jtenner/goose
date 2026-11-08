struct S{n:i64}
recursive fn make(n:i64)->S[2]{return[S{n:n},S{n:n+1}];}
fn main(){var a:S[2]=make(7);assert(a[1].n==8);print("nominal_elements");}
