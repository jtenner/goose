struct S{n:f64}recursive fn make()->S{return S{-0.0};}recursive fn read(p:f64&)->f64{return 1.0/p;}fn main(){assert(read(make().n)<0.0);print("f64_zero");}
