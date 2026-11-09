struct S{n:i64}recursive fn make()->S{return S{n:7};}recursive fn sum(p:i64&,q:S,x:i64)->i64{return p+q.n+x;}fn main(){assert(sum(make().n,S{11},3)==21);print("mixed_value");}
