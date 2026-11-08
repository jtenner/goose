recursive fn single()->f32[2]{return[-0.0,1.25];}
recursive fn double()->f64[2]{return[1.0/0.0,-0.0];}
recursive fn flags()->bool[2]{return[true,false];}
fn main(){var a:f32[2]=single();var b:f64[2]=double();var c:bool[2]=flags();assert(1.0/a[0]<0.0);assert(a[1]==1.25);assert(b[0]>1.0e300);assert(1.0/b[1]<0.0);assert(c[0]);assert(!c[1]);print("floats");}
