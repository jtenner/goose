fn result(a:i64[2])->i64[..3]{return -a;}fn main(){var a:i64[2]=[7,-8];let b=result(a);assert(b.len==2);assert(b[0]==-7);assert(b[1]==8);print("neg_return");}
