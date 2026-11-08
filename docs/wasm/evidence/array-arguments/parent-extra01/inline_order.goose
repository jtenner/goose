var value:i64[2]=[3,4];recursive fn later()->i64{value[0]=9;return 0;}
inline fn read(a:i64[2],x:i64)->i64{return a[0]+x;}
fn main(){assert(read(value,later())==3);assert(value[0]==9);print("inline_order");}
