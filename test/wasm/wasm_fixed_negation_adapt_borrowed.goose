recursive fn read(a:const i64[2]&)->i64[..3]{return -a;}fn main(){var a:i64[2]=[7,-8];let b=read(a);assert(b.len==2);assert(b[0] == -7);assert(b[1]==8);assert(a[0]==7);print("borrowed");}
