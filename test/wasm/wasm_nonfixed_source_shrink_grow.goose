fn main(){var a:i64[>..<]=[7,-8];var b:i64[>..]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);assert(a.pop()== -8);assert(a.len==1&&b.len==2&&b[1]== -8);print("shrink_grow");}
