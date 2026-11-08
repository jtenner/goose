fn main(){var a:u8[varint]=[73;255];var b:u8[u8]=copy(a);assert(b.len==255&&a.len==255);assert(b[0]==73&&b[254]==73);print("u8_255");}
