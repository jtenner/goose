fn same(a:i64[0])->i64[0]{return a;}fn main(){var x:i64[0]=[];let y=same(x);assert(y.len==0);print("inline");}
