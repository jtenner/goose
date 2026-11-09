struct S{n:bool} recursive fn make()->S{return S{true};} fn apply<F>()->bool{F(make().n)} fn main(){assert(apply(){p:bool& =>p});print("bool");}
