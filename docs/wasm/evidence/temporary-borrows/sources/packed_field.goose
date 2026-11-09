struct S{m:u8,n:i64,t:u16}recursive fn make()->S{return S{17,-700,4660};}recursive fn read(p:i64&)->i64{return p;}fn main(){assert(read(make().n)== -700);print("packed_field");}
