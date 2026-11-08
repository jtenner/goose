recursive fn make(n:i64)->i64[2]{return{let m=n+1;[m,m+1]};}
fn main(){var a:i64[2]=make(7);assert(a[1]==9);print("block");}
