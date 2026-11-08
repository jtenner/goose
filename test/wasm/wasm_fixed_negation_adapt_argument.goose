recursive fn take(b:i64[..3]){assert(b.len==2);assert(b[0] == -7);assert(b[1]==8);}fn main(){var a:i64[2]=[7,-8];take(-a);print("argument");}
