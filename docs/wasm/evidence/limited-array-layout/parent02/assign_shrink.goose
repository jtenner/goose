fn main(){var a:u8[..256]=[7,8];var b:u8[..3]=[1,2,3];b=a;assert(b.len==2&&b[0]==7&&b[1]==8);print("assign_shrink");}
