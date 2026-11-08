fn source(a:i64[2]&)->i64[2]&{return a;}fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=source(a);c[0]=99;assert(c.len==2&&a[0]==7&&c[0]==99);print("inline_reference");}
