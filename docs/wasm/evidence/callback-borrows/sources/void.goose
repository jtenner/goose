struct S{n:i64} recursive fn make()->S{return S{7};}var seen:i64=0;fn apply<F>(){F(make().n);} fn main(){apply(){p:i64& =>{assert(p==7);seen++;}};assert(seen==1);print("void");}
