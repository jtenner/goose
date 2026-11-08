fn main(){var a:i64[2]=[7,-8];let boxes:i64[..3][1]=[-a];let b=boxes[0];assert(b.len==2);assert(b[0]==-7);assert(b[1]==8);print("neg_array");}
