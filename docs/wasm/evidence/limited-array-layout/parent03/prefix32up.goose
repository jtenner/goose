fn main(){var a:u8[..256]=[7,8];var b:u8[..65536]=a;assert(b.len==2&&b[1]==8);print("prefix32up");}
