recursive fn make()->i64[2]{return[7,8];}
var equal:bool=make()==make();
fn main(){assert(equal);print("global");}
