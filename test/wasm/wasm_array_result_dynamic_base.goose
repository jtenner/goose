recursive fn make(n:i64)->i64[2]{var data:i64[]=[n];return[data[0],data[0]+1];}
recursive fn nested(n:i64)->i64[2]{var live:i64[]=[9];var a:i64[2]=make(n);assert(live[0]==9);return a;}
fn main(){var a:i64[2]=make(3);var b:i64[2]=nested(7);assert(a[1]==4);assert(b[1]==8);print("dynamic_base");}
