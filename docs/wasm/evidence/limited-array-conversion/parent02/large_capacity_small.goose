fn main(){var a:u8[..65536]=[7,8];var b:u8[u8]=a;assert(b.len==2&&b[1]==8);print("large_capacity_small");}
