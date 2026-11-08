fn main(){var a:u8[u8]=[7,8];var refs:u8[u8]&[1]=[a];var b:u8[u16]=copy(refs[0]);assert(b.len==2&&b[1]==8);print("reference_index");}
