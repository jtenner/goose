fn main(){var b:u8[..]=({var a:u8[..3]=[7,8];a});assert(b.len==2&&b.cap==2&&b[1]==8);print("limited_runtime");}
