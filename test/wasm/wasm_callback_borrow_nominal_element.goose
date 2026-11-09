struct S{n:i64} recursive fn make()->S[2]{return [S{7},S{8}];} fn apply<F>()->i64{F(make()[1])} fn main(){assert(apply(){p:S& =>p.n+3}==11);print("nominal_element");}
