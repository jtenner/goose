recursive fn make(n:i64)->i64[2]{[n,n+1]}
var a:i64[2]=make(7);
fn main(){assert(a[1]==8);print("global");}
