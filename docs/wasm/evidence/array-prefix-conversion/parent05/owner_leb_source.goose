fn main(){var a:u8[varint]=[73;128];print("before");var b:u8[u16]=copy(a);print("after");assert(b.len==128&&b[127]==73);}
