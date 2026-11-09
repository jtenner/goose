struct S{n:i64}var calls:i64=0;recursive fn make()->S{return S{7};}recursive fn use(p:i64&){assert(p==7);calls++;}fn main(){use(make().n);assert(calls==1);print("void");}
