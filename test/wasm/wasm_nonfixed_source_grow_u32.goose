fn main(){var a:u32[>..]=[4294967295];var b:u32[u16]=copy(a);assert(b.len==1&&b[0]==4294967295&&a[0]==4294967295);print("grow_u32");}
