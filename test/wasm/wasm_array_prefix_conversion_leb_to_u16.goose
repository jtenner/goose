fn main(){var a:i64[varint]=[7,-8];var b:i64[u16]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);print("leb_to_u16");}
