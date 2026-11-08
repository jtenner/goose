struct S{n:i64}
recursive fn read(a:S,b:S,original:S&)->i64{assert(&a .!= &b);assert(&a .!= original);a.n=9;assert(b.n==2);assert(original.n==2);return a.n;}
fn main(){var a:S=S{n:2};assert(read(a,a,a)==9);assert(a.n==2);print("isolation");}
