struct S{x:i64}var calls:i64=0;recursive fn make()->S{calls++;return S{7};}fn main(){-make();assert(calls==1);print("struct");}
