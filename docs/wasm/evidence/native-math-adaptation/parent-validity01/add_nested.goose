struct Box{b:i64[..3]}fn main(){var a:i64[2]=[7,-8];let box=Box{b:a+a};let b=box.b;assert(b.len==2);assert(b[0]==14);assert(b[1]==-16);print("add_nested");}
