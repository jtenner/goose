var a:i64[2]=[7,-8];var b:i64[..3]=-a;fn main(){assert(b.len==2);assert(b[0] == -7);assert(b[1]==8);assert(a[0]==7);print("global");}
