fn main(){var a:u8[..3]=[7,8];var r:u8[..3]&=a;var b:u8[..256]=copy(r);assert(b.len==2&&b[1]==8);print("reference");}
