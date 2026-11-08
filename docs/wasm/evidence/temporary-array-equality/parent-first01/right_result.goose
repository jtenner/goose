recursive fn make()->i64[2]{return[7,8];}
fn main(){var a:i64[2]=[7,8];assert(a==make());assert(!(a!=make()));print("right_result");}
