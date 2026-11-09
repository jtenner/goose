fn main(){var a:i64[..]=[..9];a.push(7);a.push(-8);var b:i64[>..]=copy(a);var c:i64[u8]=copy(a);assert(a.cap==9&&a.len==2&&b.len==2&&c.len==2&&b[1]== -8&&c[0]==7);print("runtime_spare");}
