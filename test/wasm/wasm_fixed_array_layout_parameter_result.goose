recursive fn take(c:i64[..3])->i64[..4]{var a:i64[2]=[c[0]+1,c[1]];return a;}fn main(){var a:i64[2]=[7,-8];var c=take(a);assert(c.len==2&&c[0]==8&&c[1] == -8&&a[0]==7);print("parameter_result");}
