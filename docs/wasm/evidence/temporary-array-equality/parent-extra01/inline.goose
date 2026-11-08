inline fn make(n:i64)->i64[2]{if n==0{return[7,8];}return[n,n+1];}
fn main(){assert(make(0)==make(7));print("inline");}
