fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=[1,2,3];c=copy(a);assert(c.len==2&&c[0]==7&&c[1] == -8);print("copy");}
