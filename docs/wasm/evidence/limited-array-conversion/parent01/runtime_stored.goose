fn main(){var a:i64[..3]=[7,-8];var b:i64[..]=a;assert(b.len==2&&b[0]==7&&b[1]== -8);assert(b.cap==2);b[0]=99;assert(a[0]==7);print("runtime_stored");}
