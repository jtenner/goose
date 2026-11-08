fn apply<F>(a:i64[0])->i64[0]{return F(a);}fn main(){var x:i64[0]=[];let y=apply(x){a:i64[0]=>a};assert(y.len==0);print("callback");}
