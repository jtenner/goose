fn main(){var a:i64[2]=[7,-8];var b:i64[..3]=[1,2,3];b=-a;assert(b.len==2);assert(b[0]==-7);assert(b[1]==8);print("neg_assign");}
