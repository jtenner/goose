fn main(){var a:bool[..]=[true];var b:bool[u16]=copy(a);assert(b.len==1&&b[0]==true&&a[0]==true);print("runtime_bool");}
