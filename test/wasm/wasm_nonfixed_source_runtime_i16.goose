fn main(){var a:i16[..]=[-32768];var b:i16[u16]=copy(a);assert(b.len==1&&b[0]==-32768&&a[0]==-32768);print("runtime_i16");}
