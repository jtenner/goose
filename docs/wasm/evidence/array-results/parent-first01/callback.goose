fn apply<F>(n:i64)->i64{var a:i64[2]=F(n);a[1]}
fn main(){assert(apply(7){n=>[n,n+1]}==8);print("callback");}
