recursive fn read(a:i64[2])->i64{return a[1];}
fn main(){assert(read(default<i64[2]>())==0);print("default");}
