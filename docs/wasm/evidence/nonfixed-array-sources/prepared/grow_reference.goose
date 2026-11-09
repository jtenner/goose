fn main(){var a:i64[>..]=[7,-8];var r:i64[>..]& =a;var b:i64[u16]=copy(r);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=91;assert(a[0]==7);print("grow_reference");}
