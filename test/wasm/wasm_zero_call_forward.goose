recursive fn same(a:i64[0])->i64[0]{return a;}fn main(){var a:i64[0]=[];var b=same(a);b=same(b);same(b);assert(same(a).len==0);assert(&a .!= &b);print("forward");}
