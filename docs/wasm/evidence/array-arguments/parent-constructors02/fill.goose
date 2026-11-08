var calls:i64=0;recursive fn tick()->i64{calls++;return 7;}recursive fn read(a:i64[2])->i64{return a[0]+a[1];}
fn main(){assert(read([tick();2])==14);assert(calls==1);print("fill");}
