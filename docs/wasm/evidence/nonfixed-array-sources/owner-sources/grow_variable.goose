fn main(){var a:i64[>..]=[7,-8,900];print("before");var b:i64[u16]=copy(a);print("after");assert(a.len==3&&b.len==3);assert(b[0]==7&&b[1]== -8&&b[2]==900);}
