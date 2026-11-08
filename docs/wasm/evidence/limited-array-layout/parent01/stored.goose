fn main(){var a:u8[..3]=[7,8];var b:u8[..256]=a;b[0]=99;assert(b.len==2&&b[0]==99&&b[1]==8&&a[0]==7);print("stored");}
