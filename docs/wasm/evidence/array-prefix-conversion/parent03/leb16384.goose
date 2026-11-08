fn main(){var a:u8[u32]=[73;16384];var b:u8[varint]=copy(a);assert(b.len==16384&&a.len==16384);assert(b[0]==73&&b[16383]==73);print("leb16384");}
