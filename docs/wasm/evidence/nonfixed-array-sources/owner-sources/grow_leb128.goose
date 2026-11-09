fn main(){var a:i64[>..]=[7;128];print("before");var b:i64[varint]=copy(a);print("after");assert(a.len==128&&b.len==128);assert(b[0]==7&&b[127]==7);}
