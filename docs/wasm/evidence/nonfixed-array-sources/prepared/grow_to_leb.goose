fn main(){var a:i64[>..]=[7,-8];var b:i64[varint]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);print("grow_to_leb");}
