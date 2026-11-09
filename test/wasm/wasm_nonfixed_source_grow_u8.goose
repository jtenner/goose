fn main(){var a:u8[>..]=[255];var b:u8[u16]=copy(a);assert(b.len==1&&b[0]==255&&a[0]==255);print("grow_u8");}
