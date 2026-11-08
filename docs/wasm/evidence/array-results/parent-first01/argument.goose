recursive fn make(n:i64)->i64[2]{[n,n+1]}
recursive fn read(a:i64[2])->i64{return a[1];}
fn main(){assert(read(make(7))==8);print("argument");}
