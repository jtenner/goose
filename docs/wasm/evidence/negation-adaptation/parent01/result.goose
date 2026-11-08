recursive fn result(a:i64[2])->i64[..3]{return -a;}fn main(){let b=result([7,-8]);assert(b.len==2);assert(b[0] == -7);assert(b[1]==8);print("result");}
