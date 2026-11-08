recursive fn make()->i64[2]{var a:i64[2]=[7,-8];defer{a[0]=99;}return a;}fn main(){var c:i64[]=make();assert(c.len==2&&c[0]==7&&c[1] == -8);print("defer_result");}
