recursive fn make(n:i64)->i64[2]{return[n,n+1];}
fn main(){assert(make(7)==make(7));assert(make(7)!=make(8));print("both_result");}
