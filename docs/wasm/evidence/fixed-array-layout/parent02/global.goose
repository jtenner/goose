var a:i64[2]=[7,-8];var c:i64[..3]=a;fn main(){c[0]=99;assert(c.len==2&&c[0]==99&&a[0]==7);print("global");}
