fn main(){var a:u8[..256]=[7,8,9];var b:u8[..3]=a;assert(b.len==3&&b[2]==9);print("exact_shrink");}
