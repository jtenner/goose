struct S{n:i64}
recursive fn make()->S{return S{n:7};}
fn main(){assert(make().n==7);print("struct_field");}
