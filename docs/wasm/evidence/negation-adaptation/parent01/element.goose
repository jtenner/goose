fn main(){var a:i64[2]=[7,-8];let b:i64[..3][1]=[-a];assert(b[0].len==2);assert(b[0][0] == -7);assert(b[0][1]==8);print("element");}
