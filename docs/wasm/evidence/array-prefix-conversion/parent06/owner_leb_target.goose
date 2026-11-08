fn main(){var a:u8[u16]=[73;128];print("before");var b:u8[varint]=copy(a);print("after");assert(b.len==128&&b[127]==73&&a.len==128&&a[127]==73);}
