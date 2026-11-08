fn apply<F>(a:u8[..3])->u8[..256]{F(a)}fn main(){var a:u8[..3]=[7,8];var b=apply(a){p=>p};assert(b.len==2&&b[1]==8);print("callback");}
