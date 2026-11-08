var a:u8[u8]=[7,8];var b:u8[u16]=copy(a);fn main(){assert(b.len==2&&b[1]==8);b[0]=99;assert(a[0]==7);print("global");}
