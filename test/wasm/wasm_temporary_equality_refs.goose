recursive fn make(p:i64&)->i64&[2]{return[p,p];}
fn main(){var a:i64[]=[7];var b:i64[]=[7];assert(make(a[0])==make(a[0]));assert(make(a[0])!=make(b[0]));print("refs");}
