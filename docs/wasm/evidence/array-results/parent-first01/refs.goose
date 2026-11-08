recursive fn make(p:i64&)->i64&[2]{return[p,p];}
fn main(){var data:i64[]=[7];var a:i64&[2]=make(data[0]);a[1]++;assert(data[0]==8);assert(a[0]==8);print("refs");}
