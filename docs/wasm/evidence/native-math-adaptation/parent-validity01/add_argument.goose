fn consume(b:i64[..3]){assert(b.len==2);assert(b[0]==14);assert(b[1]==-16);}fn main(){var a:i64[2]=[7,-8];consume(a+a);print("add_argument");}
