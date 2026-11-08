fn main(){var a:i64[2]=[7,-8];let boxes:i64[..3][1]=[a+a];let b=boxes[0];assert(b.len==2);assert(b[0]==14);assert(b[1]==-16);print("add_array");}
