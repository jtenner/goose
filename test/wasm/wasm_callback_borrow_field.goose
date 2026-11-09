struct S{n:i64} recursive fn make()->S{return S{7};}fn apply<F>()->i64{F(make().n)} fn main(){assert(apply(){p:i64& =>p+3}==10);print("field");}
