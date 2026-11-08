fn apply<F>(n:i64)->bool{F(n)==F(n)}
fn main(){assert(apply(7){n=>[n,n+1]});print("callback");}
