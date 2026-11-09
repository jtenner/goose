struct S{a:u8,n:i64,b:u16} recursive fn make()->S{return S{17,-700,4660};} fn apply<F>()->i64{F(make().n)} fn main(){assert(apply(){p:i64& =>p}== -700);print("packed");}
