struct Box{b:i64[..3]}fn main(){var a:i64[2]=[7,-8];let box=Box{b:-a};let b=box.b;assert(b.len==2);assert(b[0]==-7);assert(b[1]==8);print("neg_nested");}
