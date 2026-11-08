fn main(){var a:u8[u16]=[73;127];var b:u8[varint]=copy(a);assert(b.len==127&&a.len==127);assert(b[0]==73&&b[126]==73);print("leb127");}
