struct S{n:i64}recursive fn make()->S{return S{n:7};}recursive fn read(p:i64&)->i64{return p;}fn main(){assert(read(make().n)==7);print("borrow_field");}
