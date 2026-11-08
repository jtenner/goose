recursive fn make(a:u8[..3])->u8[..256]{return a;}fn main(){var a:u8[..3]=[7,8];var b=make(a);assert(b.len==2&&b[1]==8);print("return");}
