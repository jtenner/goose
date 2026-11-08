inline fn make(n:i64)->i64[2]{[n,n+1]}
fn main(){var a:i64[2]=make(7);assert(a[1]==8);print("inline");}
