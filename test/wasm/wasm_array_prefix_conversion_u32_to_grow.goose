fn main(){var a:i64[u32]=[7,-8];var b:i64[>..]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);b.push(99);assert(b.len==3&&b[2]==99);print("u32_to_grow");}
