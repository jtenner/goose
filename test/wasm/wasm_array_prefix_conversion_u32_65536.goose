fn main(){var a:u8[varint]=[73;65536];var b:u8[u32]=copy(a);assert(b.len==65536&&a.len==65536);assert(b[0]==73&&b[65535]==73);print("u32_65536");}
