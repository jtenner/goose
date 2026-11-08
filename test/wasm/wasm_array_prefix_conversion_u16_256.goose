fn main(){var a:u8[varint]=[73;256];var b:u8[u16]=copy(a);assert(b.len==256&&a.len==256);assert(b[0]==73&&b[255]==73);print("u16_256");}
