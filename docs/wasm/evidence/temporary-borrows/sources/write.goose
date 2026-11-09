struct S{n:i64}recursive fn make()->S{return S{n:7};}var calls:i64=0;recursive fn set(p:i64&){assert(p==7);p=99;assert(p==99);calls++;}fn main(){set(make().n);assert(calls==1);print("write");}
