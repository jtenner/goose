recursive fn read(a:i64[2])->i64{return a[0]+a[1];}
fn main(){var a:i64[2]=[3,4];assert(read(a)==7);print("direct");}
