recursive fn source(a:const i64[2]&)->const i64[2]&{return a;}fn main(){let a:const i64[2]=[7,-8];var c:i64[..3]=source(a);c[0]=99;assert(a[0]==7&&c[0]==99);print("readonly");}
