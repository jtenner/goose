recursive fn make(n:i64)->i64[2]{return if n>0{[n,n+1]}else{[0,1]};}
fn main(){var a:i64[2]=make(7);var b:i64[2]=make(0);assert(a[1]==8);assert(b[1]==1);print("conditional");}
