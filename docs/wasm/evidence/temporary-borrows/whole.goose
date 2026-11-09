struct S{n:i64}recursive fn make()->S{return S{n:7};}recursive fn read(p:S&)->i64{return p.n;}fn main(){assert(read(make())==7);print("borrow_whole");}
