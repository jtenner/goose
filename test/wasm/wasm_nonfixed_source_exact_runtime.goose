fn main(){var a:i64[..]=[..9];a.push(7);a.push(-8);var b:i64[..]=copy(a);assert(a.cap==9&&b.cap==9&&b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);print("exact_runtime");}
