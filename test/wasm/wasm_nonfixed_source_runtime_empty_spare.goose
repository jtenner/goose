fn main(){var a:i64[..]=[..9];var b:i64[>..]=copy(a);var c:i64[u8]=copy(a);assert(a.cap==9&&a.len==0&&b.len==0&&c.len==0);print("runtime_empty_spare");}
