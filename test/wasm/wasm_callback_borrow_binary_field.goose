struct S{n:i64} recursive fn make()->S{return S{7};}fn apply<F>()->i64{F((make()+S{2}).n)} fn main(){assert(apply(){p:i64& =>p}==9);print("binary_field");}
