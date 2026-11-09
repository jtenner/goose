recursive fn make()->i64[2]{return [7,8];}fn apply<F>()->i64{F(make()[1])} fn main(){assert(apply(){p:i64& =>p+3}==11);print("element");}
