fn main(){var a:u8[u16]=[73;128];var b:u8[varint]=copy(a);assert(b.len==128&&a.len==128);assert(b[0]==73&&b[127]==73);print("leb128");}
