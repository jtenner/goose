recursive fn make(n:i64)->i64[2]{[n,n+1]}
recursive fn forward(n:i64)->i64[2]{return make(n);}
fn main(){var a:i64[2]=forward(7);assert(a[1]==8);print("forward");}
