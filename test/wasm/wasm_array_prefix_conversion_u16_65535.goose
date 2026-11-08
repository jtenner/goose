fn main(){var a:u8[u32]=[73;65535];var b:u8[u16]=copy(a);assert(b.len==65535&&a.len==65535);assert(b[0]==73&&b[65534]==73);print("u16_65535");}
