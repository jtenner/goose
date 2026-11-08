struct S{n:i64}
recursive fn make(a:i64[2])->S{return S{n:a[0]+a[1]};}
fn main(){var a:i64[2]=[3,4];var s:S=make(a);assert(s.n==7);print("nominal_result");}
