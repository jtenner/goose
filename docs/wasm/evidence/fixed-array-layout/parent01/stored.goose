fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=a;assert(c.len==2&&c[0]==7&&c[1] == -8);c.push(99);assert(c.len==3&&c[2]==99&&a[0]==7);print("stored");}
