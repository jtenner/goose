var original:i64[2]=[3,4];recursive fn read(a:i64[2])->i64{return a[1];}
var result:i64=read(original);
fn main(){assert(result==4);print("global");}
