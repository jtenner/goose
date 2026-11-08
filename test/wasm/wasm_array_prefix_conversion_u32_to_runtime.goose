fn main(){var a:i64[u32]=[7,-8];var b:i64[..]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);assert(b.cap==2);print("u32_to_runtime");}
