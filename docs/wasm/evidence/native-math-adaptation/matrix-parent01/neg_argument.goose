fn consume(b:i64[..3]){assert(b.len==2);assert(b[0]==-7);assert(b[1]==8);}fn main(){var a:i64[2]=[7,-8];consume(-a);print("neg_argument");}
