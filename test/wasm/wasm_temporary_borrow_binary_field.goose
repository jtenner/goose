struct S{n:i64}recursive fn make()->S{return S{7};}recursive fn read(p:i64&)->i64{return p;}fn main(){assert(read((make()+S{2}).n)==9);print("binary_field");}
