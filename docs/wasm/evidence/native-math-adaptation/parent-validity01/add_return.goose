fn result(a:i64[2])->i64[..3]{return a+a;}fn main(){var a:i64[2]=[7,-8];let b=result(a);assert(b.len==2);assert(b[0]==14);assert(b[1]==-16);print("add_return");}
