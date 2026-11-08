fn main(){var a:i64[u8]=[7,-8,900];print("before");var b:i64[u16]=copy(a);print("after");assert(b.len==3&&b[0]==7&&b[1]== -8&&b[2]==900&&a.len==3&&a[0]==7);}
