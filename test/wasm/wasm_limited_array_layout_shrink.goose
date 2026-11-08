fn main(){var a:u8[..256]=[7,8];var b:u8[..3]=a;assert(b.len==2&&b[1]==8);print("shrink");}
