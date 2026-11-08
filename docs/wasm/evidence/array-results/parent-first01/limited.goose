recursive fn make(n:i64)->i64[..4]{return[n,n+1];}
fn main(){var a:i64[..4]=make(7);assert(a.len==2);assert(a[1]==8);a.push(9);assert(a.len==3);print("limited");}
