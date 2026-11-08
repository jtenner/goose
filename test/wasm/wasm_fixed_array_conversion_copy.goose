fn main(){var a:i64[2]=[7,-8];var c:i64[]=a;assert(c.len==2&&c[0]==7&&c[1] == -8);c[0]=99;assert(a[0]==7&&c[0]==99);print("copy");}
