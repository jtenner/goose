recursive fn read(a:i64[..3])->i64{assert(a.len==2);return a[0]+a[1];}
fn main(){var a:i64[..3]=[3,4];assert(read(a)==7);print("limited");}
