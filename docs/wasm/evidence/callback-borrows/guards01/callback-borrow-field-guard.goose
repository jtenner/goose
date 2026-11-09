struct S{n:i64} recursive fn make()->S{return S{7};} fn apply<F>()->i64&{F(make().n)} recursive fn read(p:i64&)->i64{return p;} fn main(){assert(read(apply(){p:i64& =>p})==7);print("guard");}
