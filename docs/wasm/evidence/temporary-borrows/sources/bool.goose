struct S{n:bool}recursive fn make()->S{return S{true};}recursive fn read(p:bool&)->bool{return p;}fn main(){assert(read(make().n));print("bool");}
