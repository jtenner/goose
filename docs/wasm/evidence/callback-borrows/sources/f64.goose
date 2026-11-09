struct S{n:f64} recursive fn make()->S{return S{-0.0};} fn apply<F>()->f64{F(make().n)} fn main(){assert(apply(){p:f64& =>1.0/p}<0.0);print("f64");}
