recursive fn make()->i64[2]{var a:i64[2]=[3,4];defer{a[1]=9;}return a;}
fn main(){var a:i64[2]=make();assert(a[1]==4);print("defer");}
