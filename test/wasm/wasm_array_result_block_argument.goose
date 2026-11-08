recursive fn read(a:i64[2])->i64{return a[1];}
fn main(){assert(read({let n:i64=7;[n,n+1]})==8);print("block_argument");}
