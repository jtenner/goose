fn main(){var a:i64[>..]=[];var b:i64[..]=copy(a);assert(a.len==0&&b.len==0);assert(b.cap==0);print("grow_empty_to_runtime");}
