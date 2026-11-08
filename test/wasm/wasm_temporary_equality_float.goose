recursive fn make(n:f64)->f64[2]{return[n,1.25];}
recursive fn single(n:f32)->f32[2]{return[n,1.25];}
fn main(){assert(make(-0.0)==make(0.0));assert(single(-0.0)==single(0.0));var zero:f64=0.0;assert(make(zero/zero)!=make(zero/zero));print("float");}
