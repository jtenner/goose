fn main(){var a:i64[..3]=[7,-8];var ref:i64[..3]& =a;var b:i64[..]=copy(ref);assert(b.len==2&&b[0]==7&&b[1]== -8);assert(b.cap==2);b[0]=99;assert(a[0]==7);print("runtime_reference");}
