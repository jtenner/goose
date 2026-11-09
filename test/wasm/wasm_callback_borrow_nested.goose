struct I{n:i64} struct O{x:I} recursive fn make()->O{return O{I{7}};} fn apply<F>()->i64{F(make().x)} fn main(){assert(apply(){p:I& =>p.n+3}==10);print("nested");}
