struct Box{a:i64[..3]}fn main(){var a:i64[2]=[7,-8];let b=Box{-a};assert(b.a.len==2);assert(b.a[0] == -7);assert(b.a[1]==8);print("field");}
