struct I{n:i64}struct O{x:I}recursive fn make()->O{return O{x:I{n:7}};}recursive fn read(p:I&)->i64{return p.n;}fn main(){assert(read(make().x)==7);print("nested_field");}
