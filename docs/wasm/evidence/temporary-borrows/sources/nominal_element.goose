struct S{n:i64}recursive fn make()->S[2]{return[S{7},S{8}];}recursive fn read(p:S&)->i64{return p.n;}fn main(){assert(read(make()[1])==8);print("nominal_element");}
