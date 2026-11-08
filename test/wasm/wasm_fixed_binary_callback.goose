fn apply<F>(a:i64[2],b:i64[2])->i64[2]{return F(a,b);}fn main(){let c=apply([7,-8],[3,4]){a:i64[2],b:i64[2]=>a+b};assert(c[0]==10&&c[1] == -4);print("callback");}
