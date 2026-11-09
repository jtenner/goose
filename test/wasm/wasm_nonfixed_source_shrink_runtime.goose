fn main(){var a:i64[>..<]=[7,-8,99];assert(a.pop()==99);var b:i64[..]=copy(a);assert(a.len==2&&b.len==2&&b.cap==2&&b[0]==7&&b[1]== -8);print("shrink_runtime");}
