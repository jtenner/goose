struct S{n:i64} recursive fn make()->S{return S{7};}fn apply<F>()->i64{F(make().n,S{11},3)} fn main(){assert(apply(){p:i64&,q:S,x:i64=>p+q.n+x}==21);print("mixed_value");}
