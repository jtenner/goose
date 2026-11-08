fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=[1,2,3];c=a;assert(c.len==2&&c[0]==7&&c[1] == -8);c.push(99);assert(c[2]==99&&a[0]==7);print("stored");}
